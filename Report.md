How the Official History Frames Donglin (東林) as a Political Faction to Be Persecuted

Introduction 

Official historical records are responsible for recording events; in addition, they use different wording to shape personal reputations, assign blame, and describe events. In this essay, it will be discussed whether the official history, Mingshi (明史), represents Donglin (東林) primarily as a target of persecution as a political faction rather than merely as a school. By using two qhchina collocate runs and their related data and the content of Mingshi, I will show in this paper that although Mingshi preserves the traces of the academic origins of Donglin, the collocation results strongly show party-labelling and punitive verbs, thereby framing Donglin as a politicised target of persecution.

Data & Source 

The resource being analysed would be the whole Mingshi, from volume 1 to volume 332. 

The reason for analysing the whole Mingshi instead of only some volumes containing the word "donglin" is that the term "Donglin" appears scattered throughout the whole Mingshi, not only in the special volume. The Donglin factional struggles are not concentrated in only a few volumes, but are also scattered in various annals, treatises, tables, and biographies. If only focusing on sections having the word "Donglin", key passages describing people and events that do not explicitly mention the word "Donglin" might be missed. 

Processing and Method

For the preparation of the text, after loading Mingshi.txt, I asked the AI agent to use OpenCC to change the text from traditional Chinese to simplified Chinese, then split the text into sentences based on Chinese punctuation, and use Jieba to tokenized the sentences into words while still preserving multi-character names like Donglin. For the next step, only sentences with not less than 5 words (tokens) were kept to avoid noisy and ineffective fragments. 

For the extraction of the collocation, I filtered the tokens whose length is less than or equal to 2 to focus on the informative tokens and to avoid useless information, for example, the stopwords. 

For finding out the P-value, a contingency table was required; for each collocate word X, 4 types of sentences will be counted: 
(I) consist of both Donglin and word X
(II) consist of Donglin only
(III) consist of word X only
(IV) consist of neither Donglin nor word X
The P-value shows how unlikely the occurrence of (I)  would be by chance; the lower the P-value is, the greater the reasonableness of rejecting the hypothesis that Donglin and word X collocate by chance, meaning this collocation is worth studying. About strength, while the P-value shows the concentration of the two words by chance, association strength, for example, log_Dice, shows how tightly the two words associate; even with small counts of appearing near each other, the greater the number of log_Dice, the more closely the two words are connected in semantics and pragmatics.

Results 

From the collocation results, it was discovered that the words collocated with the word Donglin could reveal that Donglin was narrated as a political party in Mingshi, and it had been through political persecution, as the most recurrent collocates in the data, Mingshi, are Gu Xiancheng (顧憲成), Li Sancai (李三才), (Yu) Yuli (于玉立), and Gao Panlong (高攀龍)
Wei Zhongxian (魏忠賢), its party ( qidang 其黨), party member ( dangren 黨人), Fushe (復社), and the punitive verbs, xueji (削籍) and xueduo (削奪). 

From the collocation results, first, it reveals the leadership of Donglin. The research shows that certain names were closely collocated with and related to Donglin, for example, Gu Xiancheng, Gao Panlong, Li Sancai, and Yuli. In the collocation of Donglin, these words have a high logDice value and a low P-value, showing their high frequency and tight association with Donglin. For example, Mingshi mentioned that Gu Xiancheng and Gao Panlong were among the core members and early supporters of Donglin, and Gu Xiancheng was explicitly named as one of the lecturers of Donglin, where in Mingshi, it was written that Gu Xiancheng gave lectures at Donglin Academy (顧憲成講學東林書院). 

Secondly, through analysis of the collocation, it can be discovered that Donglin suffered political persecution. Wei Zhongxian is highly recurrent, and in Mingshi, it was recorded that "Wei Zhongxian expelled all member of Donglin" (魏忠賢盡逐東林) and “Wei Zhongxian and his cronies plotted to expel all members of the Donglin”(魏忠賢黨謀盡逐東林), showing Wei Zhongxian was one of the key participants in the political persecution towards Donglin. Also, the terms xueji (削籍) and xueduo (削奪) both have high logDice values and low P-values, showing that the simultaneous occurrence of Donglin and these terms is not by chance. These patterns support the point that Donglin was a target of removal and punishment by the Wei Zhongxian party.

Lastly, the collocation also shows that Donglin was framed as a target of persecution as a political faction rather than merely as a school. The terms for stating faction, for example, qidang (其黨) and dangren (黨人), are especially common in sentences. In the sentence run, the ratio_local values of the collocations qidang (其黨) and dangren (黨人) are both very high, showing the strong relation of the collocations with Donglin. 

But Donglin was fundamentally a literary, academic, and scholarly society; Donglinshe (東林社), through it, might have combined intellectual and political functions; it was not a political faction. Scholars at that time rarely called themselves Donglindang (東林黨); sources from that period referred to the organization as Donglinshe, where the members gave lectures, had literary gatherings, composed poetry and held scholarly discussions at the Donglin Academy. But later on, while the Donglin members re-entered the government, they had great conflict with the eunuch faction led by Wei Zhongxian; therefore, the word Donglin became increasingly politicized.

In broader narratives, the tokens containing the word dang (黨) were associated with accusations and purges, showing that in the Mingshi narrative, Donglin was framed as an organized political faction, indicating that the opposition political label of Donglin provided reasons for the political persecution at the time.

Interpretation 

When running the analysis with different methods and windows, there were differences in the data. When window=5 or window=10, it emphasises lexical sequences more; for example, human names with Donglin, or Donglin with jiangxue (講學); therefore, names dominate when using the window method. When using the sentence method, there are more action words, for example, xueji (削籍) and xueduo (削奪), or the partisan label words, for example, qidang (其黨) and dangren (黨人); this is because they usually occur somewhere in the same sentence instead of being immediately adjacent, based on the Chinese sentence structure.

Limitations

Different windows, targets, segmentation, or source selection would lead to differences in the results. A narrow window will display fixed phrases first; a wider window or sentence mode could include all the nouns, verbs and labels which are not directly connected to the target word. Changing the target word might change token boundaries and counts, therefore affecting the calculation and the data. It also might lead to a change in the key point of the research because the words themselves would contain standpoint. And using a different source would shift the emphasis. Mingshi, as an official historical document written in the Qing dynasty under the push of the Qing government, contains the standpoint of the Qing government, so if the source were changed, the standpoint might no longer be related to the Qing government.

Also, as a limitation of the analysis, the events, executions and accusations about Donglin are frequently mentioned in other texts where the case only states the participants in the case, the crime, the handling procedure, and the punishment, and the word Donglin does not appear directly. These might lead to the collocation analysis of the official position nature of Donglin and the reality of persecution towards Donglin being hard to investigate through the method of collocation and statistics.

Conclusion

Based on the analysis of the collocation of Donglin in Mingshi, it was found that the word Donglin in Mingshi highlights two main narratives: an educational institution origin centred on people like Gu Xiancheng and Gao Panlong; on the other hand, it was politicized as a faction to be persecuted. By using data to analyse the connections between the words, we could find their relevance and understand the linkage among different people, events and places, and further build historical interpretations.



Reference List

張濤. (2025). “東林”作爲一個文學社派的客觀存在——從東林黨的歷史爭議說起. 甘肅社會科學, (1), 72-80. https://doi.org/10.15891/j.cnki.cn62-1093/c.20250317.003.


