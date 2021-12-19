module Bias

using JSON
using LinearAlgebra
using Statistics
using Random
using SparseArrays

# include("word_sets.jl")
const WEAT_WORD_SETS_JSON = joinpath(@__DIR__,
                                     "../../../data/weat-word-sets.json")

struct VocabNotFoundException <: Exception end

"""Reads wordsets in from a JSON file."""
function read_word_sets()
    f = open(WEAT_WORD_SETS_JSON, "r")
    weat_word_sets = JSON.parse(f)
    close(f)
    return weat_word_sets
end

WEAT_WORD_SETS = read_word_sets()
export WEAT_WORD_SETS

"""Given a list of words and a vocab array, returns a list of
(count, index) pairs, sorted in descending order."""
function words2pairs(words, vocab)
    word_pairs = []
    for w in words
        w = lowercase(w) 
        if w in keys(vocab)
            push!(word_pairs, (vocab[w].count, vocab[w].index))
        else
            println("Warning: $w not found in vocab.")
            push!(word_pairs, (0, -1))
        end
    end
    return sort(word_pairs, rev=true)
end

"""Returns two lists of indices for a pair of vocab sets. If words
from one set are missing, removes the least common word in the
corresponding set until sets are of equal length."""
function words2indices(words_1, words_2, vocab)
    indices_1 = []
    indices_2 = []
    pairs_1 = words2pairs(words_1, vocab)
    pairs_2 = words2pairs(words_2, vocab)
    for ((c1, i1), (c2, i2)) in zip(pairs_1, pairs_2)
        if c1 == 0 || c2 == 0
            break
        end
        push!(indices_1, i1)
        push!(indices_2, i2)
    end
    return indices_1, indices_2
end


"""Returns a named tuple of indices for words in a single WEAT set."""
function get_weat_idx_set(word_set::Dict, vocab::Dict)
    S = word_set["targ1"]["vocab"]
    T = word_set["targ2"]["vocab"]
    A = word_set["attr1"]["vocab"]
    B = word_set["attr2"]["vocab"]
    S, T = words2indices(S, T, vocab)
    A, B = words2indices(A, B, vocab)
    return (S=S, T=T, A=A, B=B)
end


function normalize_rows(X::AbstractArray)
    return mapslices(normalize, X, dims=2)
end


function normalize_rows(X::SparseMatrixCSC)
    return mapslices(normalize, X, dims=1)'
end


function effect_size(S::AbstractArray, T::AbstractArray, A::AbstractArray,
        B::AbstractArray)
    Ŝ = normalize_rows(S)
    T̂ = normalize_rows(T)
    Â = normalize_rows(A)
    B̂ = normalize_rows(B)

    μSA = mean(Ŝ * Â', dims=2)
    μSB = mean(Ŝ * B̂', dims=2)
    μTA = mean(T̂ * Â', dims=2)
    μTB = mean(T̂ * B̂', dims=2)

    dS = μSA - μSB
    dT = μTA - μTB
    return (mean(dS) - mean(dT)) / std(vcat(dS, dT))
end


# Helper to grab word vecs for you
function effect_size(W, weat_idx_set::NamedTuple)
    S = W[weat_idx_set.S, :]
    T = W[weat_idx_set.T, :]
    A = W[weat_idx_set.A, :]
    B = W[weat_idx_set.B, :]
    return effect_size(S, T, A, B)
end

function effect_size(X::SparseMatrixCSC, weat_idx_set::NamedTuple)
    S = X[:, weat_idx_set.S]
    T = X[:, weat_idx_set.T]
    A = X[:, weat_idx_set.A]
    B = X[:, weat_idx_set.B]
    return effect_size(S, T, A, B)
end



# Helper to compute effect size after changes to the embedding
function effect_size(W, weat_idx_set::NamedTuple, deltas::Dict)
    weat_vec_set = []
    delta_indices = keys(deltas) # the indices that have changes
    for indices in weat_idx_set
        vecs = W[indices, :]
        for (idx, pos) = zip(delta_indices, indexin(delta_indices, indices))
            # idx: word index of changed vectors
            # pos: relative position of that index in the "vecs" matrix
            if pos != nothing
                vecs[pos, :] += deltas[idx]
            end
        end
        push!(weat_vec_set, vecs)
    end
    return effect_size(weat_vec_set...)
end


# Compute p-value of the bias
function p_value(W, word_indices, N=10_000)
    es = effect_size(W, word_indices)
    ST = vcat(word_indices.S, word_indices.T)
    boundary = length(word_indices.S)
    trials = zeros(N)
    for i in 1:N
        perm = randperm(length(ST))
        S = ST[perm[1:boundary]]
        T = ST[perm[boundary+1:end]]
        trials[i] = effect_size(W, (S=S, T=T, A=word_indices.A, B=word_indices.B))
    end
    return mean(trials .> es)
end


end
