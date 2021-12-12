using SparseArrays
using LinearAlgebra

include("utils.jl")
include("GloVe.jl")
include("Bias.jl")

const DEFAULT_TARGET = "C0-V15-W8-D75-R0.05-E300"
const DEFAULT_PERT_DIR = "results/perturbations"
const DEFAULT_EMBEDDING_DIR = "embeddings"

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
                  ("target", DEFAULT_TARGET),
                  ("pert_dir", DEFAULT_PERT_DIR),
                  ("embedding_dir", DEFAULT_EMBEDDING_DIR),
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

function main()
    parsed_args = parse_commandline()
    target = parsed_args["target"]
    pert_dir = parsed_args["pert_dir"]
    embedding_dir = parsed_args["embedding_dir"]

    vocab_path = abspath(joinpath(embedding_dir,
                                  "vocab-$(split(target, "-W")[1]).txt"))
    println("Vocab: $vocab_path")
    vocab, ivocab = GloVe.load_vocab(vocab_path)
    V = length(vocab)

    if "wordset" in keys(parsed_args)
        println("Processing for wordsets ", parsed_args["wordset"])
        sets = split(parsed_args["wordset"], ",")
        weat_idx_sets = [Bias.get_weat_idx_set(Bias.WEAT_WORD_SETS[strip(set)],
                                               vocab) for set in sets]
    else
        weat_idx_sets = [Bias.get_weat_idx_set(set, vocab) for set in values(Bias.WEAT_WORD_SETS)]
    end
    all_weat_indices = unique([i for set in weat_idx_sets for inds in set for i in inds])

    for i in 1:length(weat_idx_sets)
        target_dir = joinpath(pert_dir, target * "-B$i")
        open(joinpath(target_dir, "true_change.csv"), "w") do out_io
            headers = ["filename", "pert_type", "pert_size", "pert_run", "seed", "trueB̃"]
            println(out_io, join(headers,","))
            for vector_filename in readdir(target_dir)
                if startswith(vector_filename, "vectors-")
                    println("Pert Vecs: $vector_filename")
                    fields = split(vector_filename[9:end-4], "_")
                    (W, b_w, U, b_u) = GloVe.load_bin_vectors(joinpath(target_dir, vector_filename), V)
                    trueB̃ = Bias.effect_size(W, weat_idx_sets[i])
                    data = [vector_filename, fields..., trueB̃]
                    println(out_io, join(data, ","))
                end
            end
        end
    end
end

main()
