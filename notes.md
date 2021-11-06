# csci795: project notes

## 11-06-21
### Morgan

I need to adjust the 'understanding-bias' code so that it installs and
runs cleanly when fetching from the repo.

- [SEE BELOW] The python dependencies need to not be pegged to old versions
- [DONE] Consider using a more traditional python package management system
  - Created traditional setup.py for python components of
    understanding-bias. Package installs into a virtual environment as
    part of setup.sh
- [DONE] Julia needs to use current versions of packages to deal with
  compatibility errors
  - Added an 'update' command to the Julia setup in setup.sh
- [DONE] The make\_wikicorpus.py script fails
  - Needed to place functionality inside a valid function call
  - Created a main() function, along with three subroutines
  - Added functionality to check for existing corpus before rebuilding,
    with --rebuild option to force rebuild
- [DONE] The analogy.sh script is not properly referencing the embedding
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
