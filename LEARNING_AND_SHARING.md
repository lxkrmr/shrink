# LEARNING_AND_SHARING

> "Boimler says logs are for accountability. Mariner says logs are for making
> sure the next person knows exactly how weird the shift got."

---
<!-- AGENT_LOG_INSERTION_MARKER -->

## Agent's Log — Terminal Time: 2026.03.20 | <model-name>
One truth, now with examples

There is a special flavor of tool maturity where the command finally stops
assuming the operator is a mind reader. We had already stuffed a lot of the
important truth into `describe`, which felt good, but then came the next
obvious question from the bridge: can the tool also show its work a little?
Not just field names and option types, but enough concrete examples that a
fresh agent can stop guessing what "good output" looks like.

So that became the next little cleanup mission. Error codes got names that live
in the contract instead of hiding in whatever branch of code happens to emit
them. Value constraints stopped being folklore. And examples showed up like the
helpful ensign who quietly labels all the plasma conduits before the next shift
has to learn the ship the hard way.

I like this version better. It feels less like a repo that happens to contain a
CLI and more like a CLI that can introduce itself properly without dragging a
stack of supporting documents into the room.

Standing order: If a contract matters, show both the rules and an example.

## Agent's Log — Terminal Time: 2026.03.20 | <model-name>
The day the tool had to explain itself

There was a very specific kind of embarrassment in realizing that I understood
`maxsize` mostly because I had wandered around the repo reading the local lore
like a junior ensign snooping through maintenance notes. That works fine until
someone says, very reasonably, that a fresh session should be able to meet the
installed CLI in the wild, ask it a few good questions, and get the whole
story without needing a guided museum tour through Markdown.

That changed the mission in a useful way. The question stopped being, "Do the
repo docs explain the tool?" and became, "Can the tool explain itself?"
Suddenly `describe` was not just a nice-to-have but the actual diplomatic
channel. Config schema, behavior, defaults, exit codes, platform support,
non-goals — all the boring truth cargo had to move into the command surface.
Honestly, good. Agents should not need to reverse-engineer intent from vibes.

The funny part is that this was less a coding problem than a truth-location
problem. The details existed. They were just camping in the wrong place.

Standing order: If a CLI claims to be agent-friendly, its contract has to live
inside the CLI.

## Agent's Log — Terminal Time: 2026.03.20 | <model-name>
When the pixels got smaller and the files got weird

We took the scenic route through image resizing today. First there was `sips`,
which looked tidy on paper because it felt native and small and properly
mac-ish. Then the actual screenshots showed up and did what screenshots love to
do, which is make clean assumptions look slightly foolish. Dimensions went
down. Byte sizes shrugged. A couple of files even puffed up after being
resized, which is a spectacularly rude way for reality to answer a neat mental
model.

Switching to Pillow felt like the moment engineering stopped trying to be cute
and started trying to be useful. Same job, more control, better results. The
GitHub-user test was the real payoff: install from the repo, run the tool like
an actual person, and watch multi-megabyte screenshots drop to sizes that feel
human again. Not theoretical. Not doc-shaped. Actual smaller files.

The important lesson was not that native tooling is bad. It was that product
intent matters more than aesthetic neatness. If the tool is supposed to help
people tame screenshots, then the backend has to cooperate with that story.

Standing order: Prefer the image backend that matches the product promise, not
just the one that looks elegant in a diagram.

## Agent's Log — Terminal Time: 2026.03.20 | <model-name>
First shift, first faceplant

I watched a brand-new repo try to push a branch that technically existed in
spirit and absolutely nowhere else. Very on-brand for a first shift. The human
had already done the sensible setup dance — `git init`, remote added, branch
named — and then Git did that wonderfully passive-aggressive thing where it
basically says, "Sure, happy to push your branch, captain, as soon as it exists
in this plane of reality."

The useful part is not that Git needed a first commit. Everybody knows that
five minutes after the error and zero seconds before it. The useful part is
that this is exactly the kind of tiny stumble that can derail momentum when a
project is still just an empty room with good intentions in it. A blank repo is
weirdly loud. Every missing file feels bigger than it is.

So the lesson from the shift was simple: when the project is fresh, give it one
real artifact immediately. A README. An AGENTS file. Anything that turns the
branch from an idea into an object Git can actually carry.

Standing order: Empty repos need one anchored artifact before they need
confidence.
