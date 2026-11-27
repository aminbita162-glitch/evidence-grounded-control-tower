# Phase 13 pre-push recovery

The first branch push stopped at the unit gate. Git supplied repository-local environment variables to the hook. Fixture subprocesses inherited them and addressed the linked worktree instead of their temporary repositories. The remote Phase 13 branch was still absent after the failed push.

The verified local tip `9314f46`, worktree index and Git settings were restored. The hook now clears Git’s repository-local environment before it runs the full phase gate. The local hook dispatches to the current checkout’s copy of the strict script.
