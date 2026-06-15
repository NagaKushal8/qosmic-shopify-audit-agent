# EVAL_LOOP.md

## Start from the one constraint, because it decides everything

The eval has to score an audit for a store it has never seen, and there is no answer
key. We will keep pointing it at brand new stores, so we can never build a "correct
report" to grade against. That single fact rules out the tempting design, which is one
LLM that reads the whole report and gives it a score out of ten. That design fails in
exactly the places we care about. It trusts the citations instead of checking them, so
made up evidence sails straight through. It likes confident writing more than findings
that are actually true. And it is non deterministic, so two runs of the same report give
two different numbers and you can never tell a real improvement from noise. So the eval
is layered, and on purpose most of the layers are plain Python with no model in them.
The model shows up only in the two spots where judgment is genuinely needed, and even
there it is boxed into a single yes or no question. The architecture is the eval. The
LLM is a small, caged part inside it.

## The layers, and why each one earns its place

**Layer 1, structure (Python, milliseconds).** The free floor. Ten experiments, all
four sections, every field filled, all five pillars present and not badly skewed,
confidence and lift as real numbers in sane bounds and not the word "high". None of this
needs intelligence, and most weak reports quietly die right here (a missing decision
rule on three experiments, or seven Conversion and one Retention). Catch the
embarrassing stuff first, before spending a cent on anything else.

**Layer 2a, does the evidence even exist (Python, the important cheap one).** Every
experiment points at an artifact we captured, a screenshot or a page. We check one
thing: is that file actually in the run's manifest. It is a plain set membership test,
and it catches the single worst failure mode, invented evidence, at zero model cost. An
agent that cites `pdp_mobile.png` when no such file was ever crawled fails instantly.
Fabricated evidence is the one thing Qosmic called disqualifying, so we catch it with the
cheapest check we own.

**Layer 2b, does the evidence support the claim (LLM, caged).** This is where a model
finally earns its keep, and also where it usually goes wrong, so we cage it hard. It
never sees the whole report. We hand it exactly one claim and exactly one screenshot and
ask one question: does this image support this claim, supported or contradicted or not
visible. "No price on the product page" against that page's screenshot, look, is the
price there or not. Narrow questions are where models are reliable. "Is this a good
report" is where they turn into vibes. So instead of one fuzzy score we run many tiny
grounded checks, and the fraction that come back supported is our headline number,
grounding precision. It needs no answer key, only the report and the pixels it claims to
describe.

**Layer 3, coverage (mostly Python).** For each high value page we captured, did the
report actually engage it in a pillar that plausibly applies. A product page we
screenshotted that no AOV experiment ever touched is a flag. This is the eval side answer
to "did we miss a twist". It turns a blind spot into a number that drops instead of a
hole nobody sees.

**Layer 4, is it slop (LLM, caged again).** The clever part is the question, not the
code. Slop is generic by nature, an experiment you could paste into any store. So we ask
whether this exact experiment could apply unchanged to almost any store. If yes, it is
boilerplate, not a finding grounded in this store's evidence. Genericness is our best
automatic proxy for the slop failure.

## One blended number is the wrong default, so we resist it

Averaging everything into a single score lets a tidy report buy its way out of fake
evidence. A report that grounds half its claims but nails the schema would beat one that
grounds almost everything but skewed its pillars, and that is backwards. Some failures
are gates, not gradients. So the order is gates first, then a profile, then one number
only at the very end.

**Gates come before any score exists.** Cite evidence that does not exist, miss a pillar
entirely, or ship fewer than ten experiments, and the report is capped and flagged as
broken. You cannot average your way out of fabricated evidence.

**The profile is the real output.** Five independent dimensions: grounding, specificity,
coverage, structural integrity, pillar balance. This is what we read day to day, because
"v2 grounding went up but coverage dropped" is something you can act on, while "v2 scored
78 versus 74" is not.

**The single number comes last, only for ranking,** when you need to sort twenty reports
or say whether v2 beat v1. Grounding gets the heaviest weight (0.40) because it is the
one tied to the disqualifying failure and the one that travels best to unseen stores.
Structure is lightest, because getting it right is table stakes, not a differentiator.
The weights are a judgment call, not a truth, so we check them against the one labeled
example we have, described below.

## How it actually improves, with a real example

Because there is no answer key, the eval's real job is comparing, not grading. You cannot
say a report is a 7, but you can say v2 grounds 90 percent of its claims and v1 grounded
60. That comparator is the whole engine.

Concrete run. You audit fifteen stores and store every profile. Each report looks fine on
its own, but the aggregate shows coverage stuck around 0.43 across all of them, and the
detail says the same thing every time: carts get captured but almost never used by
Retention experiments. That is not one bad report, that is a systematic bug in the
harness. You change one line in the Retention playbook, telling it the cart is primary
Retention evidence, rerun the same fifteen stores, and coverage moves from 0.43 to 0.71
while grounding holds steady. The comparator confirmed a real gain and confirmed nothing
else regressed, with no golden answer anywhere in sight.

Before we trust any of this, we prove the eval can tell good from bad. We score a known
good report against a deliberately broken copy of it, citations stripped, all one pillar,
generic text. If the good one does not clearly win, the eval is what is broken, not the
report. Passing that check is how we earn the right to turn it loose on a store we have
never seen. This is also where the provided `target_report.md` belongs: not as a scoring
target (it does not generalize), but as the labeled example that validates the evaluator.

## The two loops, and why humans fade out

There are two loops, and people conflate them. The first improves the harness: the
profile across many stores exposes a pattern, you make a targeted fix, the comparator
confirms it. Fast, and no humans needed. The second improves the eval itself: a human
spot checks a report and catches slop the eval missed (say a "post purchase email"
experiment that is generic in its mechanism even with the real store names left in). That
catch becomes a new sub check, gets validated against the known good report, and is
folded in for good. The eval grows its own rule set from real misses, and that set only
ever gains coverage. It is a ratchet.

That is why the human surface shrinks. Month one, a person reviews most flagged reports.
Month three, the structural, citation, and coverage layers never need anyone, so humans
only look at the disagreements between the eval and a spot check, plus they ratify the
occasional new rule. The honest claim is not zero humans. A new store will always surface
a new failure, so the second loop never quite reaches zero. The claim is that the cost
per report trends toward zero while the cost per genuinely new failure type stays small
and rare. That is a curve a CTO believes. "Zero humans in three months" is one they do
not.

## The one thing we are not measuring

None of this proves an experiment would actually make the store more money if it shipped.
That needs real A/B results from merchants fed back into the loop, which is the true north
star and the only thing that closes it for good, months out. Grounding precision tells
you a finding is true, not that it will win. Saying that out loud is more honest, and more
convincing, than pretending the two are the same thing.
