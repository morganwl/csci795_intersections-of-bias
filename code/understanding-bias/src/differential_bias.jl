"""
usage:
julia --project differential_bias.jl _vectors.bin_ _corpus.txt_ _output.csv_
"""

using Distributed
@everywhere using Dates
@everywhere using SparseArrays
@everywhere using LinearAlgebra

include("utils.jl")
include("Corpora.jl")

include_everywhere("GloVe.jl")
include_everywhere("Bias.jl")

PRINT_EVERY = 1_000
const DEFAULT_EMBEDDING = "embeddings/vectors-C0-V20-W8-D25-R0.05-E15-S1.bin"
const DEFAULT_CORPUS = "corpora/simplewikiselect.txt"
const DEFAULT_OUTPUT = "results/diff_bias-C0-V20-W8-D25-R0.05-E15-S1.csv"

"""Parses command line arguments and returns a Dict with arguments or
default values."""
function parse_commandline()
    # I couldn't get ArgParse to work so I'm having to do this by hand

    # list of valid arguments for each type of valid argument
    options = [
               "wordset",
              ]
    flags = []
    # positional arguments are tuples of the argument name and the
    # default value. if the default value is nothing, arguments are
    # treated as required
    positional = [
                  ("embedding", DEFAULT_EMBEDDING),
                  ("corpus", DEFAULT_CORPUS),
                  ("out_file", DEFAULT_OUTPUT),
                 ]

    # Parse optional arguments and flags
    parsed_args = Dict()
    positionals = []
    expecting = nothing    # set this when expecting to consume the next argument
    for arg in ARGS
        if !isnothing(expecting)
            parsed_args[expecting] = arg
            expecting = nothing
            continue
        end
        if startswith(arg, "--")
            option = arg[3:end]
            println(option)
            if option in options
                expecting = option
                continue
            end
            if option in flags
                parsed_args[option] = true
                continue
            end
        end
        push!(positionals, arg)
    end
    for i in 1:length(positional)
        if i <= length(positionals)
            parsed_args[positional[i][1]] = positionals[i]
        else
            parsed_args[positional[i][1]] = positional[i][2]
        end
    end
    return parsed_args
end

function pre_compute(M, X, word_indices)
    num_words = length(word_indices)
    H = Dict{Int64,Array{Float64,2}}()
    G = Dict{Int64,Array{Float64,1}}()
    for i in word_indices
        H[i] = inv(GloVe.∇²Li(M.U, X, i))
        G[i] = GloVe.∇Li(M.W, M.b_w, M.U, M.b_u, X, i)
    end
    return H, G
end


function make_job_list(corpus; first=1, last=2^62)
    # Eventually should allow prcessing subsets
    return first:min(corpus.num_documents, last)
end


function queue_jobs(corpus, job_channel, job_list)
    println("$(now()) - Started queuing jobs.")
    flush(stdout)
    open(corpus.corpus_path) do f
        for doc_num in job_list
            # println("made $doc_num")
            doc = Corpora.get_text(f, corpus, doc_num)
            put!(job_channel, (doc_num, doc))
        end
    end
    println("All jobs queued.")
end


function handle_results(out_file, results, num_jobs, wordsets)
    println("$(now()) - Started handling results.")
    println("Outfile: $(abspath(out_file))")
    i::Int64 = 1
    headers = vcat(["pid", "doc_num"], ["ΔBIF_$x" for x in wordsets])
    open(out_file, "w") do f
        println(f, join(headers, ", "))
        while (i <= num_jobs)
            # println("handled $i")
            pid, doc_num, ΔBIF = take!(results)
            println(f, "$pid, $doc_num, " * join(ΔBIF, ", "))
            if (i == 1 || i % PRINT_EVERY == 0)
                println("$(now()) - Results from job $(i)")
                flush(stdout)
                flush(f)
            end
            i += 1
        end
    end
    println("Handled all results.")
    flush(stdout)
end


@everywhere function percent_diff_bias(document, M, X, inv_hessians, gradients, weat_idx_sets,
                           effect_sizes)
    # Make the IF approximation
    target_indices = unique([i for set in weat_idx_sets for inds in set for i in inds])
    deltas = GloVe.compute_IF_deltas(document, M, X, target_indices, inv_hessians, gradients)
    # Compute the bias change
    B̃ = [Bias.effect_size(M.W, set, deltas) for set in weat_idx_sets]
    return [100 * (b - b̃) / b for (b, b̃) in zip(effect_sizes, B̃)]
end


@everywhere function run_worker(jobs, results, M, X, inv_hessians, gradients, weat_idx_sets,
                            effect_sizes)
    pid = myid()
    println(stdout, "Starting worker $(pid)")
    flush(stdout)
    while true
        if !isready(jobs)
            println(stdout, "Worker $(pid) waiting for jobs...")
            flush(stdout)
        end
        (doc_num, doc) = try take!(jobs)
        catch
            break # Channel has been closed
        end

        ΔBIF = percent_diff_bias(doc, M, X, inv_hessians, gradients, weat_idx_sets,
                                   effect_sizes)
        put!(results, (pid, doc_num, ΔBIF))
    end
    println(stdout, "Ending worker $(pid)")
    flush(stdout)
end

function build_word_sets(vocab, wordsets)
    """Takes a list of wordset keys and creates WEAT sets (named tuple
    containing S, T, A, B sets) referencing vocab by index."""
    weat_idx_sets = []
    for word_set in wordsets
        try
            push!(weat_idx_sets,
                    Bias.get_weat_idx_set(Bias.WEAT_WORD_SETS[word_set],
                                         vocab))
        catch e
            if isa(e, KeyError)
                println("Ignoring $word_set because of missing vocab.")
            else
                throw(e)
            end
        end
    end
    all_weat_indices = unique([i for set in weat_idx_sets for inds in
                               set for i in inds])
    return weat_idx_sets, all_weat_indices
end

function main()
    # Read command-line arguments
    # embedding_path = get(ARGS, 1, DEFAULT_EMBEDDING)
    # corpus_path = get(ARGS, 2, DEFAULT_CORPUS)
    # out_file = get(ARGS, 3, DEFAULT_OUTPUT)
    parsed_args = parse_commandline()
    embedding_path = parsed_args["embedding"]
    corpus_path = parsed_args["corpus"]
    out_file = parsed_args["out_file"]

    println("Computing Differential Bias")
    # Load model and corpus
    print("$(now()) - Loading model and corpus... ")
    M = GloVe.load_model(embedding_path)
    corpus = Corpora.Corpus(corpus_path)
    println("Done.")
    println("Vocabulary: $(M.vocab_path) ($(M.V) words)")
    println("Embedding: $(M.embedding_path) ($(M.D) dimensions)")
    println("Corpus: $(corpus.corpus_path) ($(corpus.num_words) tokens, $(corpus.num_documents) docs)")

    # WEAT BIAS
    if "wordset" in keys(parsed_args)
        wordsets = [strip(wordset) for wordset in split(parsed_args["wordset"],
                                                        ",")]
    else
        wordsets = keys(Bias.WEAT_WORD_SETS)
    end
    weat_idx_sets, all_weat_indices = build_word_sets(M.vocab, wordsets)
    
    # Print effect sizes and p-values for unperturbed embedding
    println('.')
    effect_sizes = [Bias.effect_size(M.W, set) for set in weat_idx_sets]
    println('.')
    p_values = [Bias.p_value(M.W, set) for set in weat_idx_sets]
    println("WEAT effect sizes: $effect_sizes")
    println("WEAT p-values: $p_values")

    # Load cooccurrence matrix
    print("$(now()) - Loading cooccurrence matrix... ")
    cooc_path = "$(dirname(embedding_path))/cooc$(match(r"-C[0-9]+-V[0-9]+-W[0-9]+", embedding_path).match).bin"
    X = GloVe.load_cooc(cooc_path, M.V, all_weat_indices)
    println("Done.")
    println("Cooc: $(abspath(cooc_path)) ($(nnz(X)) nnz)")

    # Precompute Hessians and Gradients
    print("$(now()) - Precomputing Hessians and Gradients... ")
    inv_hessians, gradients = pre_compute(M, X, all_weat_indices)
    println("Done.")

    # Setup for parallel computations
    jobs = RemoteChannel(()->Channel{Tuple{Int64, String}}(100))
    results = RemoteChannel(()->Channel{Tuple}(100))
    job_list = make_job_list(corpus)

    # Asynchronously estimate differential biases for each document
    # Output results to out_file as subprocesses complete
    @sync begin
        @async queue_jobs(corpus, jobs, job_list)

        for p in workers()
            @async remote_do(run_worker, p, jobs, results, M, X, inv_hessians, gradients, weat_idx_sets, effect_sizes)
        end

        @async handle_results(out_file, results, length(job_list), wordsets)
    end

    close(jobs)
    close(results)
    println("$(now()) - Done.")
end

main()
