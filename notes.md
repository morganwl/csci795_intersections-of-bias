# csci795: project notes

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
    - [ ] Identify mechanism for specifying WEAT vocab sets and
      abstract to command line or configuration file if necessary
        - WEAT vocab sets are hard-coded in word_sets.jl
        - [ ] Read vocab sets from configuration file
        - [ ] Specify vocab sets from command-line or configuration file
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
