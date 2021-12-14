# csci795: project notes

## 12-14-21
### Morgan

I built out the list of WEAT sets from the Tan paper and modified
Bias.jl to pull WEAT sets from a JSON document instead of a hardcoded
Julia script. I might need to update the other Julia programs if they
ever reference the WEAT_WORD_SETS directly.

## 12-13-21
### Morgan

I have started gathering WEAT tests from a variety of locations across
the internet. In the process, I have turned over a bunch of new research
that might be good to read. There is the risk that it will make us feel
foolish in our own goals.

Many of the sets are duplicates, and others are not entirely in the
format needed for our project. I came across Sentence Embedding
Association Tests, and those are quite interesting, but for another
time!

I've collected my unorganized findings in weat.txt. Some are references
to supllemental files. I have done my best to keep links inline, as well
as adding any websites or repos to the Zotero library.

- [X] Gather a bunch of WEAT sets
- [X] Organize WEAT sets
- [X] Collate WEAT sets in json file
- [X] Convert WEAT sets from json to Julia (using a quick python script)
  or adapt Julia script to load tests from a json file.

## 12-12-21
### Morgan

Rebecca got the NYT corpus in, so I need to prep it for
understanding-bias. Then I need to start pulling in WEAT tests.

- [X] Potentially modify nyt corpus script
- [X] Assemble NYT corpus for GloVe
- [X] Train word embedding on NYT corpus (this will probably take a
  while, use Josephine's desktop)
- [ ] ~~Write README for using the various understanding-bias scripts~~
- [X] Start collating WEAT tests from as many sources as possible.

## 11-26-21
### Morgan

I need to continue understanding and potentially modifying the
Understanding Bias code.

- [ ] Read and document the code for "construct perturbation sets" step
    - [ ] make_perturbations.jl
        - Numerous syntax errors
            - DataFrames now index as df[!, col] or df[:, col]. ! =
              references original column in df. : = creates copy of
              column.
            - I changed all instances to [!, col].
                - Need to find a way to check that this is correct
                  behavior
            - DataFrame sorting syntax changed slightly
            - vecnorm() is now just norm()
        - [ ] Currently uses number of hard coded wordsets. I need to change
          to use the number of word sets used in a given differential
          bias results file.
          - Just using 1 wordset for now
        - This program runs pretty quickly. Maybe a minute or two.
    - [ ] add_perturbations.jl
    - [ ] pert_pred_bias.jl
        - Not sure exactly what this program does, but I added support
          for specifying WEAT sets on the command line!
            - A better implementation would allow the selected WEAT sets
              to carry across from the initial runthrough to the final
              command. For now, I will probably implement this in a
              python front-end.
    - [ ] pert_true_bias.jl
        - Added support for specifiying WEAT sets on the command line
        - Relies on new embeddings created by scripts/reemebed.sh
    - [ ] reembed.sh
        - scripts/reembed.sh _target_ _pert-dir_ _embedding-dir_
        - Operates on a single perturbation target at a time (ie, one
          WEAT set)
        - Trains with 5 seeds
        - I imagine this will be commensurate in time with creating the
          initial embeddings
            - This trains 5 new embeddings __for each perturbation
              file__, which is a lot of new embeddings
            - make_perturbations.jl makes 30 perturbations for each WEAT
              set, which means reembed.sh will make 150 embeddings for
              each WEAT set. With the 15 iteration "toy" embedding, this
              runs at about 90 seconds per embedding, for a total of
              3.75 hours.
[ ] Read and document the code for "approximate the differential bias"

## 11-16-21
### Morgan

Very hasty changes to differential_bias.jl to support specifying WEAT
word sets from the command line. Done with minimal knowledge of
programming in Julia. I was not able to get the stock ArgParse package
working, so threw together my own sloppy alternative.

- Edited word_sets.jl to store word_sets in a dictionary instead of a
  NamedTuple.
    - Made changes to Bias.jl and tests to properly reference
      dictionary. (differential_bias.jl never addressed WEAT sets by
      name, simply iterating over all sets in word_sets.jl)
- Wrote a command line parsing function to extract options from
  command line arguments before processing positional arguments.
  Arguments can be specified as "options" (optional arguments
  expecting an additional argument), "flags" (optional arguments
  that do not expect an additional argument) and "positional"
  (expected arguments that may have default values and therefor not
  be required.)
    - Parsed arguments are returned in a dictionary meant to match
      the dictionary that would have been returned by ArgParse
- usage: julia --project src/differential\_bias.jl [_embedding.bin_]
  [_corpus.txt_] [_output.csv_] [--wordset set1[,set2,set3,...]]

If there is time, it would be good to go in and clean up and improve
the structure of this entire script.

## 11-14-21
### Morgan

I need to make sense of the main program loop for running the
understanding-bias experiment. It appears that the primary code is in
Julia; what sequence of Julia programs am I supposed to run? How do I
select the embedding/corpus to use? How do I select which vocabulary
sets to use for WEAT tests? How is information output and should we
collect that information for our own experiments?

#### Understanding Bias Experiment Procedure

1. Generate training corpus(es)
    - The make_wiki_corpus script is used to generate a corpus from
      simplewiki; a default snapshot from 2017 is used, though a more
      modern snapshot could be substituted
    - [ ] Create a process for generating a corpus from the NYT archive
        - Rebecca exploring this using NYT article metadata API
2. Train word embedding(s) using each experimental corpus
    - Train 10 baseline embeddings using a different random seed
    - The embed.sh script uses GloVe to create embeddings. It can be
      customized with a configuration file.
    - [ ] Document embed.sh
    - [ ] Create customization files for our needs
3. Aproximate the differential bias of each document
    - Estimated time: 30 seconds per WEAT set per thousand articles,
      meaning 20 minutes for the 2017 simplewiki corpus
    - The differential_bias.jl script is used to approximate biases
    - The differential bias is approximated once for each baseline, and
      then averaged together for a final value.
        - [ ] What is the variance of these values? Can we get away with
          using fewer baselines?
    - [X] Identify mechanism for specifying WEAT vocab sets and
      abstract to command line or configuration file if necessary
        - WEAT vocab sets are hard-coded in word_sets.jl
        - [ ] ~~Read vocab sets from configuration file~~
            - I think we can live with hardcoded word sets for now, as
              long as we can choose which ones to use at runtime
        - [X] Specify vocab sets from command-line or configuration file
    - [X] Identify mechanism for specifying baseline embeddings and
      abstract to command line or configuration file if necessary
        - Embedding and corpus used is specified on the command line,
          with hardcoded defaults
    - [X] Identify output mechanism
        - Estimated effect size for each document is output as a line in
          a csv file
    - [X] Document differential_bias.jl
4. Construct perturbation sets
5. Approximate the differential bias of each perturbation set
6. Construct ground truth and assess

## 11-06-21
### Morgan

I need to adjust the 'understanding-bias' code so that it installs and
runs cleanly when fetching from the repo.

- [SEE BELOW] The python dependencies need to not be pegged to old versions
- [X] Consider using a more traditional python package management system
    - Created traditional setup.py for python components of
    understanding-bias. Package installs into a virtual environment as
    part of setup.sh
- [X] Julia needs to use current versions of packages to deal with
  compatibility errors
    - Added an 'update' command to the Julia setup in setup.sh
- [X] The make\_wikicorpus.py script fails
    - Needed to place functionality inside a valid function call
    - Created a main() function, along with three subroutines
    - Added functionality to check for existing corpus before rebuilding,
      with --rebuild option to force rebuild
- [X] The analogy.sh script is not properly referencing the embedding
  files
    - Added vocab argument, required in analogy.sh, to setup.sh
    - analogy.sh cds into the GloVe directory, but points to arguments
      relative to understanding-bias directory. Added '../' to paths.

We should probably be using understanding-bias as a submodule with a
forked repo, but I've never done that in Git before, so I just
downloaded a source snapshot and treated it as part of our project.

Things I'd like to do in the future, but probably aren't urgent:
- Consolidate shell-script elements into the python package management
- Create a venv at the hunter project root and get understanding-bias to
  install properly into that
- Check for dummy embedding files before skipping the embedding step
- Just, like, generally clean up and improve the modularity /
  modifiability of this whole thing.
