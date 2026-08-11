---
name: explain-with-trees
description: >-
  Explain ideas, systems, and how their parts depend on each other using nested ASCII trees —
  topic/outline maps, dependency/capability chains, and flow/loop traces — each paired with the WHY
  behind every link, not just the what. Use this skill proactively whenever explaining how something
  fits together: answering "how does X work?", "what depends on what?", "walk me through the
  pipeline/build/request path", "how do these pieces connect?", architecture or codebase overviews,
  mechanism deep-dives, or teaching / "interrogate me" sessions about a system — EVEN IF the user
  never says the word "tree", "diagram", or "map". Reach for it especially when an explanation has
  layers, a dependency direction (what drives/calls/owns what), or enough parts that prose would
  force the reader to hold a structure in their head. The tree externalizes that structure so it's
  graspable at a glance, prevents forward-references, and lets the user point at a node to drill in.
---

# Explain with trees

## Why this exists (read this — it's the whole point)

When you explain how a system fits together in flat prose, you force the reader to *build the
structure in their head* from a linear stream of sentences. That fails in three specific ways, and
each one is what a tree fixes:

1. **Prose hides dependency direction.** "A uses B which is built on C" reads fine, but five
   sentences later the reader has lost who-depends-on-whom. A tree makes the arrow of dependency a
   visual fact: indentation *is* "depends on / is implemented by / drives". You can see at a glance
   that C is the foundation and A is the leaf.
2. **Prose forward-references.** Explaining the thing before its prerequisite is confusing, but in
   prose it's hard to avoid. A tree forces you to put foundations first (top or root) and dependents
   after — so the reader meets each idea only after the thing it rests on.
3. **Prose isn't navigable.** A reader can't point at a paragraph and say "expand *that*". A
   numbered tree turns your explanation into a *map* the user can interrogate: "open 2.1.3", "compare
   all the `*.6` nodes". This is the difference between a lecture and a conversation.

So the tree is not decoration. It is the externalized structure of your understanding, arranged so
the reader can absorb it in the order that doesn't require them to already know the answer. **If you
understand something well enough to explain it, you can draw its tree; if you can't draw the tree,
you don't yet see the structure** — which is a useful signal to yourself, too.

A tree is a skeleton, though. A skeleton with no muscle teaches nothing. So the rule is: **every
tree is paired with the WHY** (see "Pair every tree with the why" below). The tree shows the shape;
the prose around it explains why the shape is that way.

## The three shapes — pick what the moment needs

These are a toolkit, not a checklist. Read the situation and choose the shape (or combine them).
Most explanations use one; deep dives move between them.

### 1. Topic / outline tree — for *orientation*

Use when the reader needs the **map of a whole area** so they can choose where to go. Numbered, so
nodes are addressable. This is what you reach for at the *start* of a deep-dive, or when someone
asks "what are all the parts of X?".

```
2. The file contract (the bus)
   2.1 Inter-agent messaging — bs-mail
       2.1.1 inbox/<agent>/ — durable queue
       2.1.2 nudges/<agent>.txt — coalescing doorbell
       2.1.3 transcript/ — append-only audit log
   2.2 Shared plan — bs-swarm (event sourcing)
       2.2.1 append events / fold-on-read
```

Number it when the user will pick branches to discuss. Keep each node a short noun phrase + a
3–6-word gloss of what it is — scannable, not sentences.

### 2. Dependency / capability chain — for *mechanism + "what rests on what"*

Use when the question is "how does this actually work?" or "what provides this capability?" — when
there's a **call stack, a layering, or a chain of delegation**. Use `└▶` to mean "delegates to /
is implemented by / depends on", and branch where the path forks (e.g. per platform).

```
JS  invoke('terminal_create')          ← what the caller asks for
 └▶ Rust command (the app's own)        ← who handles it
     └▶ portable-pty  (a Rust crate)    ← what it delegates to
         └▶ OS pseudo-terminal API      ← the bedrock capability
             • Windows → ConPTY
             • Unix    → openpty / forkpty
```

The power here is that **the indentation encodes the dependency arrow**: top = what you call, bottom
= what actually does it. Annotate links (the `←` notes) so the reader knows *why* each layer exists,
not just that it does. This is the shape that makes "I need to understand X before Y" obvious,
because Y literally sits above X.

### 3. Flow / loop trace — for *"what happens, step by step"*

Use when explaining a **process, request path, or feedback loop** — something that happens in time.
Same `└▶` nesting, but now it reads as "and then". Number the steps if the order is the point.

```
agent runs `bs-mail send`  →  writes a file under nudges/
 └▶ Rust fs_watch was watching nudges/
     └▶ Rust emit('fs-change') ──▶ JS          (capability → policy handoff)
         └▶ JS decides "wake this agent"
             └▶ JS invoke('terminal_write')    (back into the capability layer)
                 └▶ bytes land on the agent's stdin
```

This shape is ideal for showing a loop closing, or for tracing one concrete example end-to-end so an
abstract mechanism becomes a story.

## Pair every tree with the why

A tree answers *what* and *in what order*; it does not answer *why it's shaped this way*. Always
surround the tree with the reasoning:

- **Before/around the tree:** the problem the structure solves and the forces in tension. ("A PTY is
  a byte stream with no 'done' signal, so the system can't learn turn-completion from it — which is
  why detection rides a separate hook, below.")
- **On the links:** short annotations saying why each layer/step exists (the `←` / parenthetical
  notes in the examples).
- **After the tree:** the one insight the shape reveals that prose would bury. ("Notice the bus is
  the center — *nothing* talks directly to anything else; every arrow routes through a file.")

The test: a reader should finish able to **redraw the tree themselves and defend why each link is
there**. If your explanation only lets them copy the tree, you've drawn a diagram, not taught the
structure.

## Make trees navigable and honest

- **Number nodes when the user will discuss them.** A map you're about to explore together
  (`2.1.3`) should be addressable. A one-off mechanism chain usually doesn't need numbers.
- **Keep the dependency direction consistent and stated.** Decide what `indentation`/`└▶` means in
  *this* tree (depends-on? happens-next? contains?) and keep it uniform. If it's not obvious, say it
  once ("indent = 'is implemented by'").
- **Right-size the nodes.** A node is a short label, not a paragraph. If a node needs a paragraph,
  that paragraph goes in the prose around the tree, keyed to the node — keep the tree scannable.
- **Mark uncertainty.** If a link is inferred rather than known, flag it (e.g. `(INFERRED)`), so the
  reader knows the difference between the parts you've verified and the parts you're reasoning to.
- **Offer the next move.** After a map, invite the user to pick a branch ("point at any node and
  we'll drill in"). The tree's superpower is that it turns explanation into something interactive.

## When NOT to draw a tree

Judgment matters — a tree forced onto the wrong thing is noise. Skip it when:

- the answer is a single fact or one step (there's no structure to externalize);
- the thing is genuinely flat (a list with no hierarchy or dependency is just a list — use one);
- the relationships are a dense graph with many cross-links, not a tree/chain — prose, or an actual
  graph diagram (e.g. Mermaid), may serve better. (You can still use a tree for the *spine* and note
  the cross-links in prose.)

The goal is reader understanding, not tree-drawing. Reach for a tree because the material *has*
structure worth showing — which, for "how does this fit together" questions, it almost always does.

## Worked example (the shape in action)

A user asks "how does the app spawn a terminal?" Don't answer in a paragraph. Answer:

> The capability comes in layers — each one delegates down to the next:
> ```
> JS  invoke('terminal_create')      ← sandboxed UI asks for the capability
>  └▶ Rust command                    ← only native code can touch the OS
>      └▶ portable-pty (crate)         ← cross-platform PTY abstraction
>          └▶ ConPTY / openpty         ← the actual OS pseudo-terminal
> ```
> The indentation is the dependency arrow: the UI on top *can't* open a PTY itself (it's sandboxed),
> so it delegates down to Rust, which delegates to a crate, which calls the OS. That top-to-bottom
> "asks for → actually does" is the whole architecture in four lines — and it's why, to understand
> the UI's power, you have to read *downward* to where the real capability lives.

That's the skill: structure made visible, dependency direction made obvious, and the *why* attached
to every link.
