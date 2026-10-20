# Glossary

The words this project uses for ICMA, in chat, docs, the app and conversation with Ahmed. Each
definition uses only plain English and words defined above it. Use the heading word, never the
words listed under "Don't say". Which of these words Ahmed knows is tracked in
`learning/KNOWN.md`.

Main sources: Pavlovitch, JAIS 11 (2011), pp. 143–47 (the gold study); Motzki, *Analysing Muslim
Traditions* (2010), pp. 50–56, 210–14.

## Basics

### Hadith
An account of what the Prophet said, did or approved. In this project the word also covers
accounts that stop at a Companion or a later figure; the app labels which kind it is.
- Don't say: tradition, report, khabar.

### Chain
The list of people attached to a hadith who passed it on, one to the next: "A told me that B told
him that C said … that the Prophet said". It starts with the person who wrote the hadith down and
runs back to the Prophet. Isnad is the Arabic name for it; in English prose say chain.
- Don't say: line, strand, thread, path, route, sanad.

### Narrator
One person named in a chain: someone who received the hadith and passed it on.
- Don't say: transmitter, tradent, informant, authority.

### Teacher and student
The narrator who passes a hadith on is the teacher; the narrator who receives it is the student.
Each step of a chain is one teacher passing it to one student.
- Don't say: master, pupil, source.

### Matn
The text of the hadith: the words that come after the chain and say what the Prophet said or did.
- Don't say: text (on its own), content, body.

### Version
The matn of one hadith as one chain gives it. A hadith usually survives in many versions whose
wording differs.
- Don't say: variant, recension, redaction.

### Collection
A book of hadiths, each with its chain, that survives today. A musnad is one kind of collection,
arranged by the Companion each hadith goes back to. Examples: the Ṣaḥīḥ of Muslim, the Musnad of
Ibn Ḥanbal.
- Don't say: book (as a stand-in), source, work, compilation.

### Collector
The person who compiled a collection. Every chain in a collection starts from its collector, who
names a teacher, who names a teacher, back to the Prophet.
- Don't say: author, compiler, CR.

### Earlier and later
In a chain, earlier means closer to the Prophet and later means closer to the collector.
- Don't say: above, below, upper, lower, up, down. They mean opposite things in different places
  (see Conflicts).

### Dating
Working out when a hadith first circulated. The answer is usually "by the time of narrator X",
not a year.

## Bundles and the people in them

### Bundle
All the chains of one hadith drawn together in one diagram. Where two chains name the same
narrator, they share that point in the drawing.
- Don't say: tree, graph, network, cluster.

### ICMA
Short for isnad-cum-matn analysis. A method for dating a hadith: compare its versions with its
bundle, and check whether the differences between versions follow the places where the chains
split. If they do, the narrator where the chains meet really spread the hadith, and that
narrator's version can be rebuilt and dated to that narrator's lifetime.

### Common link
The earliest narrator at whom the chains of a hadith meet. Later than the common link, the chains
spread out to many collectors; earlier, usually one chain runs back to the Prophet. Pavlovitch
adds a condition: a narrator only counts as the common link once comparing versions shows the
hadith really spread from them (see Seeming common link).
- Don't say: CL, originator, fan-out point.
- Example: in Pavlovitch's study of the ʿUbāda hadith, Shuʿba b. al-Ḥajjāj (d. 160) is the
  common link for the versions without the revelation scene.

### Partial common link
A narrator later than the common link who also passed the hadith to more than one student, so
chains meet there too. Often a direct student of the common link, but not always. A direct student
with only one student of their own is not a partial common link, and a student's student can be
one. Pavlovitch asks for the same proof as for the common link.
- Don't say: PCL.
- Example: Zayd is the common link and taught Bakr and Khalid. Bakr taught two collectors, so Bakr
  is a partial common link. Khalid taught only Hasan, so Khalid is not one. Hasan taught two
  collectors, so Hasan is one.

### Key figure
Any narrator who passed the hadith to more than one student: any point in a bundle where chains
meet. A common link or partial common link is a key figure that has passed the checks.
- Don't say: branch point, node, hub, meeting point.

### Convergence point
The key figure with the most chains in a bundle, picked automatically by the pipeline as a
starting guess. It is never a verdict. In the ʿUbāda hadith, Pavlovitch rejects it.
- Don't say: suggested CL, or "the common link" when you mean this guess.

### Branch
One student of a key figure, plus every chain that passes through that student. Two branches are
independent if they share no narrator later than the key figure, apart from the final collector.
- Don't say: leg, arm, line, path.

### Single strand
A stretch of chain where each narrator passed the hadith to only one student. Every step rests on
one person's word, and no other chain confirms it.
- Don't say: thread, line, bare strand.

### Corroborated branch
A branch that splits again later: somewhere in it a narrator passed the hadith to more than one
student, so it rests on more than one chain.
- Don't say: supported branch, confirmed branch.

## Checks and warning signs

### Seeming common link
A key figure who looks like a common link because chains meet there, but whom the checks do not
confirm. Either the bundle has the wrong shape (see Spider) or the versions do not fit together
the way real teaching would leave them.
- Don't say: SCL, false common link, apparent common link.

### Spider
A key figure from whom only single strands lead to the collectors, with no corroborated branch
anywhere later. The name is Juynboll's: the drawing looks like a body with separate legs.
Pavlovitch treats such a key figure as a seeming common link. Motzki warns that real, wide
teaching often leaves the same shape when only a few chains survive.
- Example: Pavlovitch reads the chains through ʿAlī b. al-Jaʿd in the ʿUbāda bundle as a spider,
  because no collector quotes him directly (p. 167).

### Direct quotation
A collector naming a key figure as their own teacher, with no narrator between them. Pavlovitch
treats such a step as genuine unless something specific shows otherwise, and uses its version to
test the versions that reach the same key figure through single strands (pp. 146–47).
- Don't say: unmediated quotation, direct citation, direct line.
- Example: Ibn Ḥanbal quotes Ghundar directly; Muslim reaches Ghundar through Muḥammad b.
  al-Muthannā (p. 169).

### Dive
A chain that skips a common link or partial common link and reaches a narrator earlier than them
by a different route. Juynboll treats dives as invented. Motzki argues that some are real chains
that later collectors found outside the main teaching circles.
- Don't say: bypass.

## Conflicts

Places where scholars or this codebase use a word differently from this glossary. Flag new ones
here instead of switching words.

- **Above and below.** Juynboll, Motzki and Pavlovitch draw collectors at the top, so "above the
  common link" means later. This codebase stores chains Prophet first, so "above the suggested CL"
  and `upper_paths` in `docs/tradition-package.md` mean earlier. Say earlier and later.
- **"Direct" in the code.** `pipeline/src/icma/bundle.py` labels a branch "direct" when the
  collector is the key figure's student or that student's student. A direct quotation allows no
  narrator in between. Treat them as different ideas until the spider-rule work settles it.
- **Convergence point in the code.** The field is named `suggested_cl`. Call it the convergence
  point in prose and in the app.
- **Madār in Arabic-language tools.** Classical critics and several hadith apps (Smart Hadith
  Tree, Ilm, Al-Jāmiʿ) say madār for the narrator at whom a hadith's chains meet. Some apply it to
  every such narrator, which is a key figure; others to the main one, which is closer to the
  convergence point. It does not carry Pavlovitch's checks. Say key figure or convergence point,
  whichever is meant.
