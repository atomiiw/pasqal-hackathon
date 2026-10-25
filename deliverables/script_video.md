# Video script, 4 minutes, word for word (~470 words, ~120 words per minute)

Read it as written. ▶ marks a slide change.

---

▶ **Cover**

Hi, we're team Byteskip. We put a delivery-routing problem onto Pasqal's quantum computer, a small grid of atoms controlled by lasers. Our result in one sentence: one atom per customer, placed on the chip where the customer sits on the map. That takes four, ten and fifteen atoms. The standard encoding needs fourteen, forty-five and eighty.

▶ **The problem**

A company has a few trucks, each with a weight limit, and a set of customers. We decide which customers ride together, so that customers on the same truck are close to each other. Two rules. Every customer goes on exactly one truck; that is easy to encode. No truck goes over its weight limit; that is the hard part, because the usual way to encode "no more than" is to add helper bits, and on this machine every bit is an atom.

▶ **Why the obvious encoding fails**

We started like everyone: write the cost of a plan as a formula over bits, which the machine minimises. We avoided helper bits by penalising uneven truck loads instead of overloads. That needs only four, thirty and sixty atoms. Then we tried to place the atoms, and it fails. The machine can only make two atoms interact strongly by putting them close together. But our penalty needs customers who are far apart on the map to interact strongly, so they don't end up on the same overloaded truck. Far customers would need close atoms, and close customers would need far atoms: the map turned inside out. On a flat chip that cannot be built. We measured it: on ten customers, the best placement, with our tools and Pasqal's, ranks the correct plan nine thousandth out of fifty-nine thousand.

▶ **What we changed**

So we changed what a bit stands for. Think of building each truck’s group around one customer; we call that customer the anchor. Three trucks means three anchors, one per truck, and every other customer gets attached to one of them. A bit now means “this customer is an anchor”. We put one atom per customer, placed on the customer map. Atoms that sit close together push each other apart, so two customers who are close on the map will not both become anchors. When we fire the laser and read the atoms, the ones that read 1 are the anchors, and they come out spread across the map, which is what you want: one truck per area. Then every other customer joins the nearest anchor whose truck still has room. That last step is a few lines of ordinary code.

▶ **How it runs on a real instance**

One real run: ten customers, three trucks. Where two circles overlap, those customers cannot both be centres. We sweep the laser, which gradually encourages atoms to switch on, and read a thousand times. Three hundred and five reads have exactly three centres. The most common one is here: loads twenty, nineteen, eighteen, limit twenty. And it is the best possible plan; we know, because we solved every instance exactly beforehand.

▶ **The pipeline, one command**

This is the pipeline running on a laptop, sped up. One command builds the instances, computes the exact answers, places the atoms, checks them against Pulser's device limits, searches the laser settings on the emulator, and writes the results file. Two minutes for the small size.

▶ **Results**

Share of reads that give the best plan: fifty-one to ninety-one percent on small, thirteen to twenty on medium, two to thirty-two on large. Against random bits, decoded the same way: two to four times better on small, seven to twelve on medium, over sixty on large. Against a stricter comparison, random centres: even on medium, up to eight times on large. The honest price: on medium and large, only a third to a half of the reads are usable; the rest we throw away.

▶ **Summary**

New: a weight limit with no helper bits, and an encoding where the atom layout is the customer map. Did not work: the direct formula on the bigger sizes, and half of our reads there. Everything, including the failures, is in the repository, one command to reproduce. AI wrote most of the code; the report lists its six mistakes and how we caught them. Thank you.

---

Recording: PowerPoint "Record Slide Show" or OBS, 1080p. The video slideshow (8 slides, notes = this script) is the "Byteskip video slides" artifact; its sources are in `deliverables/video_slides/`. The pipeline clip is `deliverables/run_tier_S.mp4` (GIF on the slide). Export MP4, upload to YouTube unlisted, paste the link into Devpost.
