# Python 101 - Solutions

One notebook per chapter, mirroring the exercises in the lecture notebooks.

**These are for teaching assistants, not for students.**

## How to use them

Each notebook starts with a bootstrap cell that changes the working directory to
the chapter folder, so `helpers`, `./data/...` and `./pics/...` resolve exactly
the way they do in the lectures. Just open a notebook and run it top to bottom.

Most solutions end with one or more `assert` statements, so **running a solutions
notebook is also a self-test**: if it completes without an error, every solution
in it still works against the current data and the current websites.

There is usually more than one right answer. If a student's version passes the
same `assert`, it is correct.

## Where the commentary is

The markdown cells are not a repeat of the exercise text - they say what the
exercise is actually *trying to teach*, and flag the traps students reliably fall
into. Those notes are the useful part when you are helping someone who is stuck.

## Notebooks that need the network

`07`, `08` and `09` scrape live sites (bash.hu, portfolio.hu, telex.hu, Steam,
CheapShark, vatera, amazon.de, valasztas.hu). They pass today. When one of them
breaks, that is not a bug in the solution - it means the site changed and the
matching exercise needs updating too. Which is itself the lesson of chapter IX.

## Not covered

- Chapter IX, section III (the REST API demo) points at a `bud.hu` endpoint that
  now returns 404. The method is unchanged; the example target needs replacing.
  The solutions notebook shows a working, cookie-free alternative.
- Chapters VI, VI. extra and XIII are currently skipped in the course. Their
  solutions exist but have had less classroom exposure.
