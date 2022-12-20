# Universal Dependencies used in the JDSW
_References_
* [UD Chinese](https://universaldependencies.org/zh/index.html), overview documentation for annotating modern Chinese
* [Chinese dependencies](https://universaldependencies.org/zh/dep/), guidelines for dependency annotation for modern Chinese
* [Kyoto treebank](https://github.com/UniversalDependencies/UD_Classical_Chinese-Kyoto/tree/master), the CoNLL-U data that Koichi Yasuoka's models are trained on
## Nominals
### Core arguments
#### [`nsubj`](https://universaldependencies.org/zh/dep/nsubj.html): nominal subject ✅
The verb-subject relationship in clauses like "本又作X" or "說文云X", linking "作" with "本" or "云" with "說文". Very common.
#### [`nsubj:pass`](https://universaldependencies.org/zh/dep/nsubjpass.html): passive nominal subject ❓
Occurs rarely in the Kyoto data; I don't think LDM uses the passive voice?
#### [`obj`](https://universaldependencies.org/zh/dep/obj.html): object ✅
The verb-object relationship in clauses like "本又作X" or "說文云X", linking "作" with "X" or "云" with "X". Very common.
#### [`iobj`](https://universaldependencies.org/zh/dep/iobj.html): indirect object ❓
Might occur in more complicated discursive notes? The most common phrases (pronounciations, citations, etc.) don't seem to have this, but it definitely occurs in the Kyoto data.
### Non-core dependents
#### [`obl`](https://universaldependencies.org/zh/dep/obl.html): oblique nominal ❓
Might occur in more complicated discursive notes? The most common phrases (pronounciations, citations, etc.) don't seem to have this, but it definitely occurs in the Kyoto data.
#### [`obl:agent`](https://universaldependencies.org/zh/dep/obl-agent.html): agent ❌
Seems to be specific to usage of "被" in modern Mandarin. I don't think this occurs in the JDSW. Doesn't appear in Kyoto data.
#### [`obl:patient`](https://universaldependencies.org/zh/dep/obl-patient.html): patient ❌
Seems to be specific to usage of "把" in modern Mandarin. I don't think this occurs in the JDSW. Doesn't appear in Kyoto data.
#### [`obl:tmod`](https://universaldependencies.org/zh/dep/obl-tmod.html): temporal modifier ❓
The constructions we care about don't usually seem to involve temporal modifiers, but maybe this could occur in more complicated discursive notes? Appears somewhat frequently in Kyoto data.
#### [`vocative`](https://universaldependencies.org/zh/dep/vocative.html): vocative ❌
Only occurs when you address someone directly; the JDSW obviously doesn't do this.
#### [`dislocated`](https://universaldependencies.org/zh/dep/dislocated.html): dislocated elements ❓
Not sure how to judge this for the JDSW, but it does occur occasionally in Kyoto data: for example, "魚我所欲也" from 孟子 is annotated with "欲" as the root and "魚" as a dislocated element.
#### [`disclocated:vo`](https://universaldependencies.org/zh/dep/dislocated-vo.html): dislocated object of verb-object compound ❌
Specific version of above; doesn't seem to occur in Kyoto data.
### Nominal dependents
#### [`nmod`](https://universaldependencies.org/zh/dep/nmod.html): nominal modifier ✅
Seems to be specific to usage of "的" in modern Mandarin, but occurs quite frequently in the Kyoto data, e.g. in "仁人心也" (which would probably become "仁人的心" in modern Mandarin).
#### [`appos`](https://universaldependencies.org/zh/dep/appos.html): appositional modifier ❌
Seems to describe situations where you add an additional "這裡" or "那裡" to a noun, which I think is a more modern phenomenon. Doesn't occur in Kyoto data.
#### [`nummod`](https://universaldependencies.org/zh/dep/nummod.html): numeric modifier ✅
We definitely have numbers, e.g. "一本書".
## Clauses
### Core arguments
#### [`csubj`](https://universaldependencies.org/zh/dep/csubj.html): clausal subject ❓
Not sure where this falls in the JDSW. Occurs occasionally in Kyoto data.
#### [`csubj:pass`](https://universaldependencies.org/zh/dep/csubjpass.html): passive clausal subject ❌
Same as above but passive. Doesn't occur in Kyoto data.
#### [`ccomp`](https://universaldependencies.org/zh/dep/ccomp.html): clausal complement ✅
This might occur when LDM directly quotes another author/text with "云". At the end of one annotation, we have "沈云劉音非"; I think this might be a `ccomp` relation between the "云" and the "音" i.e. "Shen says that 劉 is read '非'". 

Occurs in Kyoto data in situations like "人謂笑中有刀", where the "謂" is the root, "有" is the root of "中有刀" clause, and "有" points back to "謂" as a `ccomp` relation.
#### [`xcomp`](https://universaldependencies.org/zh/dep/xcomp.html): open clausal complement ❓
Like above, but there's no explicit subject in the clause. Might be more accurate when describing very short clauses like "斫也" in which the (implied) subject is a character in the headword?

Rare, but does occur in Kyoto data.
### Non-core dependents
#### [`advcl`](https://universaldependencies.org/zh/dep/advcl.html): adverbial clause modifier ❓
This might apply to the "quantifier" clauses, e.g. the "下同" in "於角反下同"? In this case the `advcl` relation might be between the 反 and the 同. In Kyoto data, seems to often relate "以" to other tokens.
### Nominal dependents
#### [`acl`](https://universaldependencies.org/zh/dep/acl.html): clausal modifier of noun ❓
Not sure this occurs in the JDSW. In Kyoto data, appears in constructions like "忌諸將有大功者" where the latter half is the modifying clause and "有" relates to "者" as an `acl` relation. 
## Modifier words
### Non-core dependents
#### [`advmod`](https://universaldependencies.org/zh/dep/advmod.html): adverbial modifier ✅
I think this is e.g. the "又" or "亦" in "本又作...". Very common in Kyoto data; seems to also apply to negations ("不").
#### [`advmod:df`](https://universaldependencies.org/zh/dep/advmod-df.html): duration or frequency adverbial modifier ❌
Special case of the above. Seems like it could occur, but far less common than the above. Might not be worth distinguishing. Doesn't appear in Kyoto data.
#### [`discourse`](https://universaldependencies.org/zh/dep/discourse.html): discourse element ❌
Seems like this refers to interjections, and thus only occurs in transcribed speech. Kyoto data doesn't use it.
#### [`discourse:sp`](https://universaldependencies.org/zh/dep/discourse-sp.html): sentence particle ✅
I think this describes "也" in definitions/glosses; Kyoto data also applies it to "矣". 
### Nominal dependents
#### [`amod`](https://universaldependencies.org/zh/dep/amod.html): adjectival modifier ✅
This is just a regular adjective; I'm having trouble finding one but they must occur somewhere!
## Function words
### Non-core dependents
#### [`aux`](https://universaldependencies.org/zh/dep/aux.html): auxiliary ✅
The modern chinese 了 seems like it fits this, but not sure if there's an equivalent in the JDSW. "有" and "沒有" as applied to verbs also fit in modern Chinese; not sure what/if the equivalent is in the JDSW (非? 無?) Kyoto data applies it to things like "能" "可" when paired with another verb.
#### [`aux:pass`](https://universaldependencies.org/zh/dep/auxpass.html): passive auxiliary ❌
Exclusively applies to modern chinese "被"; don't think it's relevant. Not in Kyoto data.
#### [`cop`](https://universaldependencies.org/zh/dep/cop.html): copula ✅
Exclusively applies to "是" in modern chinese, but a note also says:
> The words 為 / wéi “be, be as” and 非 / fēi “not be” are also included if they are the only verb in a sentence and the latter is semantically equivalent to the opposite of 是 shì.

...which could plausibly occur. Kyoto data does use it for "為", as in "德裕爲侍郞".
#### [`mark`](https://universaldependencies.org/zh/dep/mark.html): marker ✅
Kyoto data applies this to "之" as a possessive marker. Probably it'll also come up in the JDSW?
#### [`mark:adv`](https://universaldependencies.org/zh/dep/mark-adv.html): manner adverbializer ❌
Subcase of the above specific to "地" in modern Chinese; not sure there is an OC/MC equivalent. Not used in Kyoto data.
#### [`mark:rel`](https://universaldependencies.org/zh/dep/mark-rel.html): adjectival, relativizer, and nominalizer ❌
Subcase of the above specific to "的" in modern Chinese; we could use this for "之", but we may as well just use the more general `mark` relation. Not used in Kyoto data.
### Nominal dependents
#### [`det`](https://universaldependencies.org/zh/dep/det.html): determiner ✅
Modern 這，那，每, etc. In Kyoto data, usually appears relating "其", "吾", etc. This seems like it might occur in longer, discursive notes.
#### [`clf`](https://universaldependencies.org/zh/dep/clf.html): classifier ✅
This is e.g. the link between "一" and "本" in "一本書".
#### [`case`](https://universaldependencies.org/zh/dep/case.html): case marker ✅
Appears in Kyoto data in constructions like "無所控訴", where "所" is the case marker. Seems common enough.
#### [`case:loc`](https://universaldependencies.org/zh/dep/case-loc.html): postpositional localizer ❌
As far as I can tell, we mostly get prepositions and not postpositions (e.g. in "下及住同") so I don't think this occurs. Not used in Kyoto data.
## Coordination
#### [`conj`](https://universaldependencies.org/zh/dep/conj.html): conjunct ✅
Relationship between the two verbs in multi-clause pronounciations, e.g. "音偷又音揄" — the first "音" is coordinated with the second "音".
#### [`cc`](https://universaldependencies.org/zh/dep/cc.html): coordinating conjunction ✅
Relationship between the actual conjunction word and the conjuct, e.g. in "音偷又音揄" — the "又" is the coordinating conjunction pointing to the second "音".
## Multi-word expressions (MWE)
#### [`fixed`](https://universaldependencies.org/zh/dep/fixed.html): fixed multiword expression ✅
Rare, but does occur in Kyoto data — most often to relate the tokens in the phrase "可以", but also for strange things like "硜硜然". "可以" does seem to occur a handful of times in the JDSW. In other cases, `compound:redup` is used for reduplication like "形穆穆", although that dependency isn't in the UD spec.
#### [`flat`](https://universaldependencies.org/zh/dep/flat.html): flat multiword expression ✅
Very common in Kyoto data, e.g. for relating the tokens in "朋友". It's also sometimes used for names that consist of titles, like "桓公" in "桓公殺公子糾".
#### [`compound`](https://universaldependencies.org/zh/dep/compound.html): compound ✅
Rarer in Kyoto data, but used for expressions like "天下" where there's internal "order" to the word (as opposed to "朋友"). Like `flat`, used for names with titles, e.g. "哀公" in "告於哀公曰". Not sure what determines which gets used for names; maybe we should try to be more consistent than Kyoto data is.
#### [`compound:dir`](https://universaldependencies.org/zh/dep/compound-dir.html): directional verb compound ❌
Modern "上來" and "下去", but I don't know if there are ancient equivalents. Not used in Kyoto data.
#### [`compound:vo`](https://universaldependencies.org/zh/dep/compound-vo.html): verbal object compound ❌
Modern split verbs like “讀完書了”, but I don't know if there are ancient equivalents. Not used in Kyoto data.
#### [`compound:vv`](https://universaldependencies.org/zh/dep/compound-vv.html): verbal verb compound ❌
Modern compounds like "聽不懂", but I don't know if there are ancient equivalents. Not used in Kyoto data.
## Loose
#### [`list`](https://universaldependencies.org/zh/dep/list.html): list ❌
Sounds like this could theoretically relate all of the various clauses in an entire annotation, as though reading them out as a comma- or semicolon-separated list. I think we instead want to parse them as individual sentences.

In Kyoto data, used only to relate "第" to things in chapter titles like "子路篇第十三", which doesn't seem relevant.
#### [`parataxis`](https://universaldependencies.org/zh/dep/parataxis.html): parataxis ❌
This seems to get used in Kyoto data when a speaker is listing things off using parallel construction, e.g. "X有Y，X有Z，X有W". I don't think we want to use this for that, since we want to parse each of those as individual sentences.
## Special
#### [`orphan`](https://universaldependencies.org/zh/dep/orphan.html): orphan ❌
Occurs in modern Chinese, but I don't think it occurs in ancient Chinese? Not used in Kyoto data.
#### [`goeswith`](https://universaldependencies.org/zh/dep/goeswith.html): goes with ❌
Only used in cases where tokenization was incorrect. Not used in Kyoto data.
#### [`reparandum`](https://universaldependencies.org/zh/dep/reparandum.html): reparandum ❌
Only used to indicate hesitant speech. Not used in Kyoto data.
## Other
#### [`punct`](https://universaldependencies.org/zh/dep/punct.html): punctuation ❌
No punctuation in our data.
#### [`root`](https://universaldependencies.org/zh/dep/root.html): root ✅
Every sentence has to have one.
#### [`dep`](https://universaldependencies.org/zh/dep/dep.html): unspecified dependency ❓
Usage is discouraged; no reason to use it unless nothing else applies. Could be used as a last resort to connect tokens in a fanqie, but we could instead pick a different relation or create a custom one instead.