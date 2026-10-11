# 01 One classifier instance per process

Status: resolved
Type: bug

## Problem
`get_classifier` created the classifier lazily inside a dependency. Four concurrent first requests built four classifiers, each with its own lock, so the lock that serializes local-model calls did not protect those requests.

## Fix
The classifier is built once in the lifespan and kept on `app.state.classifier` (released on shutdown). The dependency only reads it and raises `ClassifierUnavailable` before startup completes.

## Verified by
Three tests: built once in lifespan and cleared on shutdown; 8 threads get the same object; the dependency refuses before load.
