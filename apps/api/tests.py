#encoding: utf-8

# Universal Subtitles, universalsubtitles.org
# 
# Copyright (C) 2010 Participatory Culture Foundation
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see 
# http://www.gnu.org/licenses/agpl-3.0.html.
from django.test import TestCase
from videos.models import Video, VIDEO_TYPE_YOUTUBE, SubtitleLanguage
from django.core.urlresolvers import reverse
from apps.auth.models import CustomUser as User
from django.utils import simplejson as json

# text from real data https://www.pivotaltracker.com/story/show/12101197
SRT_TEXT = u'1\r\n00:00:01,004 --> 00:00:04,094\r\nWelkom bij de presentatie é over optellen niveau 2\r\n\r\n2\r\n00:00:04,094 --> 00:00:07,054\r\nWel, ik denk dat we het beste maar meteen kunnen beginnen met enkele opgaven\r\n\r\n3\r\n00:00:07,054 --> 00:00:10,009\r\nhopelijk krijg je, terwijl we ze oplossen,\r\n\r\n4\r\n00:00:10,009 --> 00:00:13,049\r\neen beter idee van hoe je deze opgaven het beste kunt aanpakken. Eens even kijken ...\r\n\r\n5\r\n00:00:13,049 --> 00:00:18,057\r\nEven checken of dit het goede pen tooltje is. Okay.\r\n\r\n6\r\n00:00:18,057 --> 00:00:27,048\r\nStel, ik heb elf plus 4\r\n\r\n7\r\n00:00:27,048 --> 00:00:32,044\r\nEn misschien denk je nu: Hey Sal, elf plus vier, ik weet nog niet\r\n\r\n8\r\n00:00:32,044 --> 00:00:34,025\r\nhoe ik tweecijferige nummers moet optellen!\r\n\r\n9\r\n00:00:34,025 --> 00:00:35,085\r\nWel, er zijn een aantal manieren om dit soort opgaven op te lossen.\r\n\r\n10\r\n00:00:35,085 --> 00:00:39,071\r\nIk zal je eerst laten zien dat je alleen maar hoeft te weten hoe je eencijferige getallen\r\n\r\n11\r\n00:00:39,071 --> 00:00:42,007\r\nmoet optellen, en dat je dan met behulp van iets wat "onthouden" wordt genoemd [Sal noemt het "carrying" wat \'dragen\' betekent]\r\n\r\n12\r\n00:00:42,007 --> 00:00:43,024\r\nom het hele probleem op te lossen.\r\n\r\n13\r\n00:00:43,024 --> 00:00:45,060\r\nEn dan zullen we proberen om het te visualiseren zodat je goed kunt zien\r\n\r\n14\r\n00:00:45,060 --> 00:00:46,089\r\nhoe je dit soort problemen kunt aanpakken\r\n\r\n15\r\n00:00:46,089 --> 00:00:48,064\r\nen ze uit je hoofd kunt oplossen.\r\n\r\n16\r\n00:00:48,064 --> 00:00:51,085\r\nDus, wat je moet doen met dit soort opgaven, is kijken\r\n\r\n17\r\n00:00:51,085 --> 00:00:55,090\r\nnaar het meest rechtse cijfer bij de elf\r\n\r\n18\r\n00:00:55,090 --> 00:00:57,050\r\nHier staan de EENheden, ok?\r\n\r\n19\r\n00:00:57,050 --> 00:00:59,079\r\nWant deze \xe9\xe9n is \xe9\xe9n, en we noemen dit de TIENtallen\r\n\r\n20\r\n00:00:59,079 --> 00:01:03,084\r\nIk ben bang dat ik je nu in de war maak, maar dit is de manier waarop alles werkt, maar straks\r\n\r\n21\r\n00:01:03,084 --> 00:01:06,041\r\nzal alles er makkelijker uitzien.\r\n\r\n22\r\n00:01:06,041 --> 00:01:08,078\r\nDus je kijkt naar de plaats waar de EENheden staan, en je ziet dat er een \xe9\xe9n is hier\r\n\r\n23\r\n00:01:08,078 --> 00:01:11,055\r\nEn dan neem je die \xe9\xe9n en die tel je op bij het nummer daaronder\r\n\r\n24\r\n00:01:11,055 --> 00:01:13,084\r\nDus \xe9\xe9n plus vier is vijf\r\n\r\n25\r\n00:01:13,084 --> 00:01:16,026\r\nDat wist je al, toch?\r\n\r\n26\r\n00:01:16,026 --> 00:01:20,028\r\nToch? Je weet dat \xe9\xe9n plus 4 hetzelfde is als vijf\r\n\r\n27\r\n00:01:20,028 --> 00:01:21,068\r\nEn dat is alles wat ik hier heb gedaan\r\n\r\n28\r\n00:01:21,068 --> 00:01:25,073\r\nIk heb enkel gezegd dat \xe9\xe9n plus deze vier hetzelfde is als vijf\r\n\r\n29\r\n00:01:25,073 --> 00:01:27,029\r\nNu ga ik deze doen\r\n\r\n30\r\n00:01:27,029 --> 00:01:29,012\r\nDeze \xe9\xe9n plus ... wel er staat hier niets behalve een plusteken\r\n\r\n31\r\n00:01:29,012 --> 00:01:30,053\r\nen dat is geen cijfer wat je kunt optellen\r\n\r\n32\r\n00:01:30,053 --> 00:01:33,003\r\nDus \xe9\xe9n plus niets is \xe9\xe9n\r\n\r\n33\r\n00:01:33,003 --> 00:01:35,056\r\nDus zetten we hier een \xe9\xe9n\r\n\r\n34\r\n00:01:35,056 --> 00:01:39,086\r\nEn dan krijgen we elf plus vier is samen vijftien\r\n\r\n35\r\n00:01:39,086 --> 00:01:44,059\r\nEn zodat je kunt zien dat deze manier echt werkt,\r\n\r\n36\r\n00:01:44,059 --> 00:01:46,030\r\nlaten we het op verschillende manieren visualiseren\r\n\r\n37\r\n00:01:46,030 --> 00:01:48,062\r\nzodat je een goed idee krijgt van wat elf plus vier betekent\r\n\r\n38\r\n00:01:48,062 --> 00:01:54,098\r\nStel dat ik elf ballen heb, \xe9\xe9n, twee, drie, vier, vijf, zes,\r\n\r\n39\r\n00:01:54,098 --> 00:01:58,090\r\nzeven,Φ acht, negen, tien, elf.\r\n\r\n40\r\n00:01:58,090 --> 00:02:14,091\r\nDat is elf, toch? 1, 2, 3,4, 5, 6, 7, 8, 9, 10, 11. Ok ik zou het moeten doen zoals bij Sesam Straat [zingt cijfers, en maakt een fout]. Hoe dan ook, het is nog vroeg, en ik ben een beetje gek.\r\n\r\n41\r\n00:02:14,091 --> 00:02:17,043\r\nOkay, Dus dat is elf, en nu gaan we er vier bij doen\r\n\r\n42\r\n00:02:17,043 --> 00:02:22,074\r\nDus, \xe9\xe9n, twee, drie, vier\r\n\r\n43\r\n00:02:22,074 --> 00:02:25,093\r\nEn het enige wat we nu hoeven te doen is tellen hoeveel cirkels\r\n\r\n44\r\n00:02:25,093 --> 00:02:27,090\r\nof ballen we nu in totaal hebben\r\n\r\n45\r\n00:02:27,090 --> 00:02:33,083\r\nDat is \xe9\xe9n, twee, drie, vier, vijf, zes, zeven, acht\r\n\r\n46\r\n00:02:33,083 --> 00:02:39,058\r\nnegen, tien, elf, twaalf, dertien, veertien, vijftien.\r\n\r\n47\r\n00:02:39,058 --> 00:02:41,096\r\nVijftien! En ik zou je niet aanraden om het iedere keer zo te doen\r\n\r\n48\r\n00:02:41,096 --> 00:02:43,084\r\nals je een opgave hebt, want dan ben je heel lang bezig\r\n\r\n49\r\n00:02:43,084 --> 00:02:45,079\r\nMaar hey, als je het ooit niet zeker weet, is het beter om\r\n\r\n50\r\n00:02:45,079 --> 00:02:48,027\r\nlanger bezig te zijn dan om een fout te maken!\r\n\r\n51\r\n00:02:48,027 --> 00:02:50,065\r\nLaten we eens  een andere manier bedenken om dit te visualiseren\r\n\r\n52\r\n00:02:50,065 --> 00:02:52,097\r\nIk denk dat verschillende manieren om het uit te beelden\r\n\r\n53\r\n00:02:52,097 --> 00:02:54,047\r\nop verschillende manieren verschillende mensen aanspreekt\r\n\r\n54\r\n00:02:54,047 --> 00:02:56,021\r\nLaten we een nummerlijn tekenen\r\n\r\n55\r\n00:02:56,021 --> 00:02:58,000\r\nIk weet niet of je ooit eerder een nummer lijn hebt gezien maar\r\n\r\n56\r\n00:02:58,000 --> 00:03:00,093\r\nje gaat er nu in ieder geval eentje te zien krijgen\r\n\r\n57\r\n00:03:00,093 --> 00:03:03,068\r\nEn een nummer lijn, het enige wat ik daarvoor doe is\r\n\r\n58\r\n00:03:03,068 --> 00:03:04,079\r\nalle nummer op volgorde opschrijven\r\n\r\n59\r\n00:03:04,079 --> 00:03:13,089\r\nDus nul, \xe9\xe9n, twee, drie, vier, vijf, zes - ik ga ze klein opschrijven zodat ik\r\n\r\n60\r\n00:03:13,089 --> 00:03:35,041\r\nhet red om ook vijftien op te schrijven. zes, zeven, acht, negen, tien, elf, twaalf, dertien, veertien, vijftien, zestien, zeventien, achtien.\r\n\r\n61\r\n00:03:35,041 --> 00:03:36,012\r\nEnzovoorts\r\n\r\n62\r\n00:03:36,012 --> 00:03:39,024\r\nEn deze pijlen beteken dat de cijfers alsmaar doorgaan\r\n\r\n63\r\n00:03:39,024 --> 00:03:41,018\r\nin allebei de richtingen\r\n\r\n64\r\n00:03:41,018 --> 00:03:42,052\r\nIk weet dat het nog een beetje te vroeg is voor je om dit te leren, maar\r\n\r\n65\r\n00:03:42,052 --> 00:03:43,068\r\nin feite kunnen de cijfers alsmaar doorgaan\r\n\r\n66\r\n00:03:43,068 --> 00:03:45,002\r\nnaar links, zelfs onder de nul\r\n\r\n67\r\n00:03:45,002 --> 00:03:46,064\r\nIk laat je daar nog even rustig over denken\r\n\r\n68\r\n00:03:46,064 --> 00:03:48,099\r\nMaar laten we terugkeren naar de opgave\r\n\r\n69\r\n00:03:48,099 --> 00:03:52,010\r\nDus hebben we elf, laat me elf omcirkelen - eens even kijken waar elf\r\n\r\n70\r\n00:03:52,010 --> 00:03:52,085\r\nstaat op de nummerlijn\r\n\r\n71\r\n00:03:52,085 --> 00:03:55,005\r\nElf staat hier, he?\r\n\r\n72\r\n00:03:55,005 --> 00:03:56,060\r\nDit is elf\r\n\r\n73\r\n00:03:56,060 --> 00:03:58,028\r\nEn dan tellen we daar vier bij op\r\n\r\n74\r\n00:03:58,028 --> 00:04:03,002\r\nEn wanneer je vier optelt, dan betekent dat we elf vermeerderen met vier\r\n\r\n75\r\n00:04:03,002 --> 00:04:04,098\r\nDus wanneer je optelt volg je in feite de nummerlijn\r\n\r\n76\r\n00:04:04,098 --> 00:04:06,084\r\nen we gaan naar rechts op de nummerlijn\r\n\r\n77\r\n00:04:06,084 --> 00:04:08,024\r\nwant de nummers worden steeds groter\r\n\r\n78\r\n00:04:08,024 --> 00:04:15,030\r\nDus gaan we \xe9\xe9n, twee, drie, vier - tadaa!\r\n\r\n79\r\n00:04:15,030 --> 00:04:16,091\r\nEn we zijn op vijftien\r\n\r\n80\r\n00:04:16,091 --> 00:04:19,093\r\nWederom kost dit heel veel tijd, maar als je ooit\r\n\r\n81\r\n00:04:19,093 --> 00:04:23,044\r\nin de war raakt of vergeet wat \xe9\xe9n plus vier is, alhoewel ik\r\n\r\n82\r\n00:04:23,044 --> 00:04:26,062\r\nniet denk dat dat snel zou gebeuren, dan kun je het dus op deze manier proberen\r\n\r\n83\r\n00:04:26,062 --> 00:04:32,076\r\nLaten we nu eens wat moeilijkere problemen proberen\r\n\r\n84\r\n00:04:32,076 --> 00:04:42,086\r\nLaten we achtentwintig plus zeven doen\r\n\r\n85\r\n00:04:42,086 --> 00:04:46,033\r\nOkay. Acht plus zeven, ik zal je eerlijk bekennen, zelfs\r\n\r\n86\r\n00:04:46,033 --> 00:04:49,062\r\nvandaag de dag raak ik soms nog in de war van acht plus zeven\r\n\r\n87\r\n00:04:49,062 --> 00:04:53,069\r\nAls je het antwoord weet, dan kun je dit type opgaven al\r\n\r\n88\r\n00:04:53,069 --> 00:04:55,044\r\nje kunt het antwoord\r\n\r\n89\r\n00:04:55,044 --> 00:04:55,076\r\ngewoon hier opschrijven\r\n\r\n90\r\n00:04:55,076 --> 00:04:58,017\r\nEn laten we het tekenen op de nummerlijn, want ik denk\r\n\r\n91\r\n00:04:58,017 --> 00:05:01,045\r\ndat een tikkeltje extra oefening met optellen geen kwaad kan\r\n\r\n92\r\n00:05:01,045 --> 00:05:02,045\r\nop dit punt\r\n\r\n93\r\n00:05:02,045 --> 00:05:04,051\r\nDus kunnen we weer de nummerlijn tekenen\r\n\r\n94\r\n00:05:04,051 --> 00:05:08,044\r\nacht plus zeven\r\n\r\n95\r\n00:05:08,044 --> 00:05:11,056\r\nEn deze keer ga ik niet tekenen vanaf nul, ik begin bij vijf, want zoals je weet\r\n\r\n96\r\n00:05:11,056 --> 00:05:13,043\r\nals je doorgaat kom je uiteindelijk op nul\r\n\r\n97\r\n00:05:13,043 --> 00:05:28,086\r\nDus als we vijf, zes, zeven, acht, negen, tien, elf, twaalf, dertien, veertien, vijftien\r\n\r\n98\r\n00:05:28,086 --> 00:05:33,014\r\n16, 17, 18 enzovoorts\r\n\r\n99\r\n00:05:33,014 --> 00:05:35,029\r\nEn zo gaat het door tot honderd, en duizend en\r\n\r\n100\r\n00:05:35,029 --> 00:05:37,048\r\neen miljoen triljoen biljoen\r\n\r\n101\r\n00:05:37,048 --> 00:05:38,060\r\nDus wat doen we?\r\n\r\n102\r\n00:05:38,060 --> 00:05:40,044\r\nWe beginnen met acht want deze opgave is acht plus zeven\r\n\r\n103\r\n00:05:40,044 --> 00:05:44,040\r\nwe willen uitvinden wat acht plus zeven is\r\n\r\n104\r\n00:05:44,040 --> 00:05:46,051\r\nDus laten we beginnen met acht\r\n\r\n105\r\n00:05:46,051 --> 00:05:47,057\r\nEn we gaan daar zeven bij optellen\r\n\r\n106\r\n00:05:47,057 --> 00:05:49,033\r\nLaat ik van kleur veranderen\r\n\r\n107\r\n00:05:49,033 --> 00:05:57,090\r\nDus ga je 1, 2, 3, 4, 5, 6, 7\r\n\r\n108\r\n00:05:57,090 --> 00:05:59,042\r\nHey, kijk daar is de 15 weer\r\n\r\n109\r\n00:05:59,042 --> 00:06:01,094\r\nDus 8 + 7 is samen 15\r\n\r\n110\r\n00:06:01,094 --> 00:06:05,050\r\nEn naarmate je meer oefent, zul je dit soort opgaven\r\n\r\n111\r\n00:06:05,050 --> 00:06:08,080\r\nuit je hoofd leren, en weet je vanzelf dat 8+7 samen 15 is,\r\n\r\n112\r\n00:06:08,080 --> 00:06:10,070\r\nen dat 6+7 samen 13 is\r\n\r\n113\r\n00:06:10,070 --> 00:06:13,020\r\nMaar in de tussentijd kan het geen kwaad om deze nummerlijn\r\n\r\n114\r\n00:06:13,020 --> 00:06:16,010\r\nte maken want het helpt je om te visualiseren wat er gebeurt\r\n\r\n115\r\n00:06:16,010 --> 00:06:18,006\r\nEn je kunt ook cirkels gebruiken als je dat duidelijker vindt\r\n\r\n116\r\n00:06:18,006 --> 00:06:19,058\r\nDUs we weten dat 8 plus 7 15 is\r\n\r\n117\r\n00:06:19,058 --> 00:06:22,027\r\nDus we gaan een nieuw ding leren\r\n\r\n118\r\n00:06:22,027 --> 00:06:24,025\r\nJe hoeft niet de hele vijftien op te schrijven\r\n\r\n119\r\n00:06:24,026 --> 00:06:29,000\r\nJe schrijft de vijf hier op\r\n\r\n120\r\n00:06:29,000 --> 00:06:33,030\r\nEn dan die 1, die onthoud je\r\n\r\n121\r\n00:06:33,030 --> 00:06:35,017\r\nDie 1 schrijf je hier\r\n\r\n122\r\n00:06:35,017 --> 00:06:38,026\r\nIk zal in een toekomstige presentatie uitleggen waarom\r\n\r\n123\r\n00:06:38,026 --> 00:06:41,083\r\ndit werkt, en misschien heb je nu al enig idee\r\n\r\n124\r\n00:06:41,083 --> 00:06:45,086\r\nwant de 1 is in de plaats voor de tientallen, en dit is\r\n\r\n125\r\n00:06:45,086 --> 00:06:47,031\r\nde plaats voor de tientallen\r\n\r\n126\r\n00:06:47,031 --> 00:06:48,081\r\nIk wil je niet verwarren\r\n\r\n127\r\n00:06:48,081 --> 00:06:50,087\r\nDus je hebt die 1 en nu tel je die op bij\r\n\r\n128\r\n00:06:50,087 --> 00:06:54,067\r\nde twee, en krijg je 35\r\n\r\n129\r\n00:06:54,067 --> 00:06:59,006\r\nToch? Want 1 plus 2 is 3 toch?\r\n\r\n130\r\n00:06:59,006 --> 00:07:00,005\r\nEn dan ben je klaar\r\n\r\n131\r\n00:07:00,005 --> 00:07:02,008\r\n35\r\n\r\n132\r\n00:07:02,008 --> 00:07:03,075\r\nEn misschien vraag je je af, is dat logisch?\r\n\r\n133\r\n00:07:03,075 --> 00:07:06,072\r\nDat 27 plus 7 is 35\r\n\r\n134\r\n00:07:06,072 --> 00:07:09,000\r\nEn er zijn een aantal manieren waarop ik graag hierover denk\r\n\r\n135\r\n00:07:09,000 --> 00:07:12,080\r\nWel, 8 plus 7 is 15 zoals we weten he?\r\n\r\n136\r\n00:07:12,081 --> 00:07:14,013\r\nEn ik weet niet hoe makkelijk je\r\n\r\n137\r\n00:07:14,013 --> 00:07:15,000\r\nkunt rekenen met grote nummers\r\n\r\n138\r\n00:07:15,000 --> 00:07:18,050\r\nMaar 18 plus 7 - laten we eens kijken naar hoe dit moet worden opgelost\r\n\r\n139\r\n00:07:18,050 --> 00:07:22,063\r\n8 plus 7 is samen 15\r\n\r\n140\r\n00:07:22,063 --> 00:07:25,036\r\n18 plus 7 - je denkt nu misschien Sal, waar haal je die\r\n\r\n141\r\n00:07:25,036 --> 00:07:27,072\r\n18 vandaan, maar geloof mij op mijn woord\r\n\r\n142\r\n00:07:27,072 --> 00:07:30,037\r\n18 plus 7 is samen 25\r\n\r\n143\r\n00:07:30,037 --> 00:07:36,085\r\n28 plus 7 is samen 35, en dat is de opgave die we zojuist op hebben gelost\r\n\r\n144\r\n00:07:36,085 --> 00:07:38,070\r\nDat is een "check mark"\r\n\r\n145\r\n00:07:38,070 --> 00:07:41,088\r\nEn, als je door blijft gaan, stel dat je 38 plus 7 doet\r\n\r\n146\r\n00:07:41,088 --> 00:07:43,037\r\ndan is dat samen gelijk aan 45\r\n\r\n147\r\n00:07:43,037 --> 00:07:45,086\r\nJe ziet hier nu een patroon ontstaan en\r\n\r\n148\r\n00:07:45,086 --> 00:07:47,091\r\ndenk hier vooral even rustig over na\r\n\r\n149\r\n00:07:47,091 --> 00:07:49,061\r\nMisschien wil je zelfs even de video hiervoor pauzeren.\r\n\r\n150\r\n00:07:49,061 --> 00:07:52,035\r\nEen andere manier waarop je hierover zou kunnen denken\r\n\r\n151\r\n00:07:52,035 --> 00:07:57,073\r\nals je me nog steeds niet gelooft, bedenk dan dat als je 1 optelt  bij 28 je 29 krijgt\r\n\r\n152\r\n00:07:57,073 --> 00:08:01,097\r\nEn als ik 2 optel krijg ik 30, als ik 3 optel krijg ik 31\r\n\r\n153\r\n00:08:01,097 --> 00:08:05,041\r\nMet 4 erbij krijg ik 32\r\n\r\n154\r\n00:08:05,041 --> 00:08:08,042\r\nAls ik 5 optel krijg ik 33\r\n\r\n155\r\n00:08:08,042 --> 00:08:11,055\r\nMet 6 erbij krijg ik 34\r\n\r\n156\r\n00:08:11,055 --> 00:08:14,011\r\nEn als ik 7 optel krijg ik weer 35\r\n\r\n157\r\n00:08:14,011 --> 00:08:16,014\r\nOkay, alles wat ik nu heb gedaan is: ik heb steeds gekeken welk\r\n\r\n158\r\n00:08:16,014 --> 00:08:19,080\r\ncijfer ik zou krijgen als ik het nummer een tikkeltje groter zou maken\r\n\r\n159\r\n00:08:19,080 --> 00:08:20,099\r\nLaten we nog enkele opgaven bekijken, en ik denk dat we\r\n\r\n160\r\n00:08:20,099 --> 00:08:21,093\r\ner nog enkele zullen doen\r\n\r\n161\r\n00:08:21,093 --> 00:08:24,068\r\nLaten we het dit keer een tikkeltje sneller doen, omdat je\r\n\r\n162\r\n00:08:24,068 --> 00:08:26,011\r\nnu waarschijnlijk beter snapt hoe je deze opgaven moet doen\r\n\r\n163\r\n00:08:26,011 --> 00:08:27,057\r\nLaten we een moeilijkere proberen\r\n\r\n164\r\n00:08:27,057 --> 00:08:33,029\r\nLaten we 99 plus 9 doen\r\n\r\n165\r\n00:08:33,029 --> 00:08:35,039\r\nDus wat is 9 plus 9?\r\n\r\n166\r\n00:08:35,039 --> 00:08:37,066\r\nEn als je niet weet hoeveel 9 plus 9 is, kun je dit oplossen\r\n\r\n167\r\n00:08:37,066 --> 00:08:40,072\r\ndoor een nummerlijn te tekenen of door cirkels te tekenen.\r\n\r\n168\r\n00:08:40,072 --> 00:08:41,099\r\nEn hoewel dat een goede manier is, zou je uiteindelijk\r\n\r\n169\r\n00:08:41,099 --> 00:08:44,007\r\ndit soort sommen ook uit je hoofd moeten kunnen oplossen\r\n\r\n170\r\n00:08:44,007 --> 00:08:50,072\r\n9 plus 9 is samen 18.\r\n\r\n171\r\n00:08:50,072 --> 00:08:55,032\r\nEn dan schrijf je de 8 hier, en onthoud je de 1\r\n\r\n172\r\n00:08:55,032 --> 00:08:56,080\r\nEn nu tel je 1 plus 9 op\r\n\r\n173\r\n00:08:56,080 --> 00:08:58,014\r\nWel je weet wat 1 plus 9 is\r\n\r\n174\r\n00:08:58,014 --> 00:09:01,048\r\n1 plus 9 is samen 10\r\n\r\n175\r\n00:09:01,048 --> 00:09:04,063\r\nEn nu schrijf je\r\n\r\n176\r\n00:09:04,063 --> 00:09:07,046\r\nhet hele getal hier\r\n\r\n177\r\n00:09:07,046 --> 00:09:12,027\r\nDus 99 plus 9 is hetzelfde als 108\r\n\r\n178\r\n00:09:12,027 --> 00:09:15,082\r\nLaten we er nog 1 doen\r\n\r\n179\r\n00:09:15,082 --> 00:09:22,045\r\nBijvoorbeeld 56 plus 7\r\n\r\n180\r\n00:09:22,045 --> 00:09:23,077\r\nWel 6 plus 7 samen\r\n\r\n181\r\n00:09:23,077 --> 00:09:30,007\r\nWel 6 plus 7 is 13, toch?\r\n\r\n182\r\n00:09:30,007 --> 00:09:32,064\r\nAls je het verwarrend vindt, teken alles dan weer uit\r\n\r\n183\r\n00:09:32,064 --> 00:09:33,098\r\nEn dan krijg je 1 plus 5\r\n\r\n184\r\n00:09:33,098 --> 00:09:35,057\r\nen 1 plus 5 is samen 6\r\n\r\n185\r\n00:09:35,057 --> 00:09:36,096\r\n63\r\n\r\n186\r\n00:09:36,096 --> 00:09:38,076\r\nEn het is slim om zelf te proberen een aantal van dit soort problemen op te lossen\r\n\r\n187\r\n00:09:38,076 --> 00:09:41,058\r\nEn als je begrijpt wat we hebben gedaan\r\n\r\n188\r\n00:09:41,058 --> 00:09:45,005\r\nben je klaar om een aantal niveau 2 opgaven op te lossen\r\n\r\n189\r\n00:09:45,005 --> 00:09:46,058\r\nVeel plezier !\r\n'

class WebUseTest(TestCase):
    def _make_objects(self):
        self.auth = dict(username='admin', password='admin')
        self.user = User.objects.get(username=self.auth['username'])
        self.video = Video.objects.get(video_id='iGzkk7nwWX8F')

    def _simple_test(self, url_name, args=None, kwargs=None, status=200, data={}):
        response = self.client.get(reverse(url_name, args=args, kwargs=kwargs), data)
        self.assertEqual(response.status_code, status)
        return response

    def _login(self):
        self.client.login(**self.auth)

class ViewsTest(WebUseTest):
    
    fixtures = ['test.json']
    
    def test_video_read(self):
        self._make_objects()
        
        youtube_id = '066bLRRPQx8'
        video_url = 'http://www.youtube.com/watch?v=%s' % youtube_id
        
        data = {
            'video_url': video_url
        }
        url = reverse("api:0.1:video_handler")
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 401)
        
        data.update(**self.auth) 
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        video = Video.objects.get(videourl__videoid=youtube_id, videourl__type=VIDEO_TYPE_YOUTUBE)
        self.assertEqual(video.user, self.user)
        self.user = User.objects.get(id=self.user.id)
        
    def test_subtitles(self):
        youtube_id = 'uYT84jZDPE0'
        
        try:
            Video.objects.get(videourl__videoid=youtube_id, videourl__type=VIDEO_TYPE_YOUTUBE)
            self.fail()
        except Video.DoesNotExist:
            pass
        
        url = 'http://www.youtube.com/watch?v=%s' % youtube_id
        self._simple_test("api:subtitles", data={'video_url': url})
        
        try:
            Video.objects.get(videourl__videoid=youtube_id, videourl__type=VIDEO_TYPE_YOUTUBE)
        except Video.DoesNotExist:
            self.fail()
    
        self._simple_test("api:subtitles", data={'video_url': url})
        
        response = self._simple_test("api:subtitles")
        data = json.loads(response.content)
        self.assertTrue(data['is_error'])

        response = self._simple_test(
            "api:subtitles", 
            data={'video_url': url, 'callback': 'fn'})
        self.assertEquals('fn([]);', response.content)
        self.assertEquals('text/javascript', response['content-type'])
        
    def test_subtitle_existence(self):
        youtube_id = 'uYT84jZDPE0'

        try:
            Video.objects.get(videourl__videoid=youtube_id, videourl__type=VIDEO_TYPE_YOUTUBE)
            self.fail()
        except Video.DoesNotExist:
            pass
        
        url = 'http://www.youtube.com/watch?v=%s' % youtube_id
        response = self._simple_test("api:subtitle_existence", data={'video_url': url})
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        
        try:
            video = Video.objects.get(videourl__videoid=youtube_id, videourl__type=VIDEO_TYPE_YOUTUBE)
        except Video.DoesNotExist:
            self.fail()
            
        video.subtitlelanguage_set.create(language='ru', is_original=False)
        
        url = 'http://www.youtube.com/watch?v=%s' % youtube_id
        response = self._simple_test("api:subtitle_existence", data={'video_url': url})
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        
        response = self._simple_test("api:subtitle_existence")
        data = json.loads(response.content)
        self.assertTrue(data['is_error'])
    
    def test_subtitles_reading(self):
        language = 'en'
        video = Video.objects.all()[:1].get()
        lang = video.subtitlelanguage_set.all()[:1].get()
        lang.language = language
        lang.save()
        
        version = lang.latest_version()
        
        url = reverse("api:0.1:subtitle_handler")
        data = {
            'video_id': video.video_id,
            'language': language
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertEqual(len(r), len(version.subtitles()))
        
        #add one more SubtitleLanguage for same language
        new_lang = SubtitleLanguage(video=video, language=language)
        new_lang.is_original = False
        new_lang.save()
        
        #should get same subtitles because they are more completed
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertEqual(len(r), len(version.subtitles()))        
        
        #set manually language id
        data['language_id'] = new_lang.id
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertEqual(len(r), 0)        
        
    def test_subtitle_create(self):
        video_id= "iGzkk7nwWX8F"
        slang = "en"
        data = {
            "video":video_id,
            "video_language": 'en',
            "language": slang,
            "format": "srt",
            "subtitles": SRT_TEXT,
            }

        url = "%s?username=admin&password=admin" % reverse("api:0.1:subtitle_handler")
        self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        lang = video.subtitle_language(slang)
        self.assertTrue(lang)

        self.assertEquals(189, lang.subtitle_count)
        text =  lang.latest_subtitles()[0].text
        self.assertEquals(text, u'Welkom bij de presentatie é over optellen niveau 2')
        
        #test re-upload identical subtitles
        #lang has no dependent, so subtitles should be rewrited for this SubtitleLanguae
        self.assertEqual(lang.subtitlelanguage_set.count(), 0)
        self.assertFalse(lang.is_dependent())
        
        self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        self.assertEqual(video.subtitlelanguage_set.filter(language=slang).count(), 1)
        
        #add dependet SubtitleLanguage
        lang1 = SubtitleLanguage(video=video, is_original=False, language='ru', standard_language=lang)
        lang1.save()
        self.assertEqual(lang.subtitlelanguage_set.count(), 1)
        
        self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        self.assertEqual(video.subtitlelanguage_set.filter(language=slang).count(), 2)        


    def test_subtitle_update(self):
        self._make_objects()
        video_id= "iGzkk7nwWX8F"
        slang = "en"
        data = {
            "video":video_id,
            "video_language": 'en',
            "language": slang,
            "format": "srt",
            "subtitles": SRT_TEXT,
            }

        url = "%s?username=admin&password=admin" % reverse("api:0.1:subtitle_handler")
        self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        lang = video.subtitle_language(slang)
        updated_srt = "1\r\n00:00:00,008 --> 00:00:03,003\r\nHello 1.\r\n\r\n2\r\n00:00:03,003 --> 00:00:05,003\r\nHello 2.\r\n\r\n" 
        data = {
            "format": "srt",
            "subtitles": updated_srt,
            "language_id": lang.pk,
            }

        url = "%s?username=admin&password=admin" % reverse("api:0.1:language-update")
        res = self.client.post(url, data=data, follow=True)
        self.assertEquals( res.status_code, 201)        
        lang = SubtitleLanguage.objects.get(pk=lang.pk)
        self.assertEquals( res.status_code, 201)        
        self.assertEquals( lang.subtitle_count, 2)
        self.assertEquals("Hello 1.", lang.latest_subtitles()[0].text)


    def test_subtitle_create1(self):
        subtitles_string = u'1\r\n00:00:00,008 --> 00:00:03,003\r\nWitam na\nprezentacji o jednostkach.\r\n\r\n2\r\n00:00:03,003 --> 00:00:05,003\r\nZacznijmy.\r\n\r\n3\r\n00:00:05,003 --> 00:00:12,007\r\nJe\u015bli bym Ci\u0119 zapyta\u0142, albo\npowiedzia\u0142bym, \u017ce przeby\u0142em\r\n\r\n4\r\n00:00:12,007 --> 00:00:20,009\r\n0.05 kilometra -- niekt\xf3rzy\nludzie m\xf3wi\u0105 KIL-ometry\r\n\r\n5\r\n00:00:20,009 --> 00:00:22,000\r\nalbo kil-O-metry.\r\n\r\n6\r\n00:00:24,008 --> 00:00:28,002\r\nJe\u015bli pokona\u0142em 0.05\nkilometra, jak du\u017co\r\n\r\n7\r\n00:00:28,002 --> 00:00:30,008\r\ncentymetr\xf3w pokona\u0142em?\r\n\r\n8\r\n00:00:30,008 --> 00:00:32,005\r\nTo "znak zapytania"\ncentymetr\xf3w.\r\n\r\n9\r\n00:00:35,008 --> 00:00:38,003\r\nWi\u0119c, zanim zajmiemy si\u0119\nMatematyk\u0105, wa\u017cne \u017ceby po prostu\r\n\r\n10\r\n00:00:38,003 --> 00:00:41,007\r\nwiedzie\u0107 co oznaczaj\u0105\nprefiksy centy- i kilo-.\r\n\r\n11\r\n00:00:41,007 --> 00:00:44,006\r\nI dobrze by by\u0142o to zapami\u0119ta\u0107,\nlub na pocz\u0105tku\r\n\r\n12\r\n00:00:44,006 --> 00:00:46,001\r\nrobienia zada\u0144, mo\u017cesz\npo prostu napisa\u0107 to na\r\n\r\n13\r\n00:00:46,001 --> 00:00:48,000\r\nkartce papieru, tak, \u017ceby\u015b\nm\xf3g\u0142 na ni\u0105 spojrze\u0107.\r\n\r\n14\r\n00:00:48,000 --> 00:01:06,004\r\nWi\u0119c kilo znaczy 1,000, hekto\nznaczy 100, deka znaczy10.\r\n\r\n15\r\n00:01:06,004 --> 00:01:09,008\r\nTo ostatnie mo\u017cesz skojarzy\u0107\nz dekad\u0105, tj. 10 lat.\r\n\r\n16\r\n00:01:09,008 --> 00:01:13,009\r\nOraz, oczywi\u015bcie,\nbrak prefiksu oznacza 1.\r\n\r\n17\r\n00:01:13,009 --> 00:01:15,005\r\nBrak prefiksu.\r\n\r\n18\r\n00:01:15,005 --> 00:01:18,006\r\nBrak prefiksu r\xf3wna si\u0119 1.\r\n\r\n19\r\n00:01:18,006 --> 00:01:28,000\r\ndecy oznacza 0.1 lub 1/10.\r\n\r\n20\r\n00:01:28,000 --> 00:01:32,005\r\ncenty-- Ci\u0105gle zmieniam\nprzypadki.\r\n\r\n21\r\n00:01:32,005 --> 00:01:38,005\r\ncenty oznacza\n0.01, lub 1/100.\r\n\r\n22\r\n00:01:38,005 --> 00:01:45,001\r\nW ko\u0144cu, mili jest r\xf3wne\n0.001, i to jest\r\n\r\n23\r\n00:01:45,001 --> 00:01:48,006\r\nto samo co 1/1,000.\r\n\r\n24\r\n00:01:48,006 --> 00:01:52,008\r\nSpos\xf3b w jaki pami\u0119tam, mam na my\u015bli,\ncenty, je\u015bli my\u015blisz o\r\n\r\n25\r\n00:01:52,008 --> 00:01:54,007\r\nskolopendrze, ma ona sto st\xf3p.\r\n\r\n26\r\n00:01:54,007 --> 00:01:58,003\r\nStonoga, nie jestem pewien czy\nstonoga ma 1,000 st\xf3p, ale\r\n\r\n27\r\n00:01:58,003 --> 00:02:00,008\r\nto wynika ze s\u0142ow stonoga.\r\n\r\n28\r\n00:02:00,008 --> 00:02:02,005\r\nponiewa\u017c pede znaczy stopa.\r\n\r\n29\r\n00:02:02,005 --> 00:02:03,008\r\nWr\xf3\u0107my do zadania.\r\n\r\n30\r\n00:02:03,008 --> 00:02:08,004\r\nJe\u015bli mam 0.05 kilometra, ile\nmam centymetr\xf3w?\r\n\r\n31\r\n00:02:08,004 --> 00:02:10,003\r\nZawsze gdy rozwi\u0105zuj\u0119 zadanie tego\ntypu,\r\n\r\n32\r\n00:02:10,003 --> 00:02:12,009\r\nzamieniam liczb\u0119 na\nmetry poniewa\u017c s\u0105 one\r\n\r\n33\r\n00:02:12,009 --> 00:02:14,002\r\ndla mnie \u0142atwe.\r\n\r\n34\r\n00:02:14,002 --> 00:02:18,001\r\nI aktualnie, zamierzam\nskr\xf3ci\u0107 to do km, i\r\n\r\n35\r\n00:02:18,001 --> 00:02:21,005\r\nmo\u017cemy skr\xf3ci\u0107 to\ndo cm gdy mamy centymetry.\r\n\r\n36\r\n00:02:21,005 --> 00:02:28,004\r\nPowiedzmy 0.05 km.\r\n\r\n37\r\n00:02:28,004 --> 00:02:32,005\r\nC\xf3\u017c, je\u015bli chc\u0119 zamieni\u0107 to\nna metry, to b\u0119dzie\r\n\r\n38\r\n00:02:32,005 --> 00:02:37,001\r\nwi\u0119cej ni\u017c 0.05 metra\nczy mniej ni\u017c 0.05?\r\n\r\n39\r\n00:02:37,001 --> 00:02:40,008\r\nC\xf3\u017c, kilometr jest bardzo du\u017cym\ndystansem, wi\u0119c wyra\u017cony\r\n\r\n40\r\n00:02:40,008 --> 00:02:43,004\r\nw metrach, b\u0119dzie\nznacznie wi\u0119ksz\u0105 liczb\u0105.\r\n\r\n41\r\n00:02:43,004 --> 00:02:52,005\r\nWi\u0119c mo\u017cemy to pomno\u017cy\u0107\nrazy 1,000 metr\xf3w, i zrobi\u0119\r\n\r\n42\r\n00:02:52,005 --> 00:02:53,008\r\nto dziel\u0105c przez 1 kilometr.\r\n\r\n43\r\n00:02:56,004 --> 00:02:58,000\r\nI co to daje?\r\n\r\n44\r\n00:02:58,000 --> 00:03:04,008\r\nC\xf3\u017c, 0.05 razy 1,000\nr\xf3wna si\u0119 50, prawda?\r\n\r\n45\r\n00:03:04,008 --> 00:03:07,006\r\nPo prostu pomno\u017cy\u0142em\n0.05 razy 1,000.\r\n\r\n46\r\n00:03:07,006 --> 00:03:12,006\r\nPrzy jednostkach, teraz\nmam kilometry razy\r\n\r\n47\r\n00:03:12,006 --> 00:03:16,002\r\nmetry przez kilometry.\r\n\r\n48\r\n00:03:16,002 --> 00:03:18,002\r\nI kilometry si\u0119 skracaj\u0105.\r\n\r\n49\r\n00:03:18,002 --> 00:03:22,002\r\nPoniewa\u017c jeste\u015b ju\u017c zaznajomiony\nz tym,mo\u017cesz traktowa\u0107 jednostki\r\n\r\n50\r\n00:03:22,002 --> 00:03:24,006\r\ndok\u0142adnie w ten sam spos\xf3b\nw jaki traktujesz liczby\r\n\r\n51\r\n00:03:24,006 --> 00:03:25,006\r\nlub zmienne.\r\n\r\n52\r\n00:03:25,006 --> 00:03:28,009\r\nDop\xf3ki masz t\u0119 sam\u0105\njednostk\u0119 w liczniku i\r\n\r\n53\r\n00:03:28,009 --> 00:03:30,009\r\nw mianowniku, mo\u017cesz skr\xf3ci\u0107\nje, zak\u0142adaj\u0105c, \u017ce\r\n\r\n54\r\n00:03:30,009 --> 00:03:33,004\r\nnie dodajesz jednostek, mno\u017cysz jednostki.\r\n\r\n55\r\n00:03:33,004 --> 00:03:36,005\r\nWi\u0119c masz kilometry razy\nmetry dzielone przez kilometry,\r\n\r\n56\r\n00:03:36,005 --> 00:03:40,000\r\ni to si\u0119 r\xf3wna 50 metr\xf3w.\r\n\r\n57\r\n00:03:40,000 --> 00:03:43,008\r\nI zawsze dobrze jest sprawdzi\u0107\npoprawno\u015b\u0107 po ka\u017cdym kroku.\r\n\r\n58\r\n00:03:43,008 --> 00:03:45,006\r\nZwykle gdy robisz ten rodzaj\nzada\u0144, wiesz, OK, je\u015bli\r\n\r\n59\r\n00:03:45,006 --> 00:03:48,007\r\nchc\u0119 przej\u015b\u0107 od kilometr\xf3w do\nmetr\xf3w, Zamierzam u\u017cy\u0107\r\n\r\n60\r\n00:03:48,007 --> 00:03:51,000\r\nliczby 1,000, poniewa\u017c jest to\nrelacja pomi\u0119dzy\r\n\r\n61\r\n00:03:51,000 --> 00:03:52,001\r\nkilometrem i metrem.\r\n\r\n62\r\n00:03:52,001 --> 00:03:54,008\r\nI zawsze jeste\u015b zdezorientowany,\nc\xf3\u017c, mno\u017c\u0119 przez 1,000,\r\n\r\n63\r\n00:03:54,008 --> 00:03:56,002\r\nczy dziel\u0119 przez 1,000?\r\n\r\n64\r\n00:03:56,002 --> 00:03:58,007\r\nI zawsze musisz stwierdzi\u0107,\nc\xf3\u017c, je\u015bli przechodz\u0119 od\r\n\r\n65\r\n00:03:58,007 --> 00:04:03,000\r\nkilometr\xf3w do metr\xf3w, zamieniam\n-- 1 kilometr to\r\n\r\n66\r\n00:04:03,000 --> 00:04:05,005\r\n1,000 metr\xf3w, tak?\r\n\r\n67\r\n00:04:05,005 --> 00:04:07,008\r\nWi\u0119c b\u0119d\u0119\nmno\u017cy\u0142 przez 1,000.\r\n\r\n68\r\n00:04:07,008 --> 00:04:09,001\r\nOtrzymam wi\u0119ksz\u0105\nliczb\u0119.\r\n\r\n69\r\n00:04:09,001 --> 00:04:12,004\r\nI to jest pow\xf3d dla kt\xf3rego\npomno\u017cy\u0142em 0.05\r\n\r\n70\r\n00:04:12,004 --> 00:04:14,005\r\nprzez 1,000 i otrzymuj\u0119 50.\r\n\r\n71\r\n00:04:14,005 --> 00:04:16,000\r\nWi\u0119c wr\xf3\u0107my\ndo problemu.\r\n\r\n72\r\n00:04:16,000 --> 00:04:19,003\r\n0.05 kilometra jest\nr\xf3wne 50 metrom.\r\n\r\n73\r\n00:04:19,003 --> 00:04:20,001\r\nNie sko\u0144czyli\u015bmy jeszcze.\r\n\r\n74\r\n00:04:20,001 --> 00:04:23,002\r\nTeraz, musisz zamieni\u0107\n50 metr\xf3w na centymetry.\r\n\r\n75\r\n00:04:23,002 --> 00:04:25,005\r\nC\xf3\u017c, robimy to samo.\r\n\r\n76\r\n00:04:25,005 --> 00:04:32,007\r\n50 metr\xf3w razy-- ile-- wi\u0119c\njaka jest relacja pomi\u0119dzy\r\n\r\n77\r\n00:04:32,007 --> 00:04:33,007\r\nmetrami i centymetrami?\r\n\r\n78\r\n00:04:33,007 --> 00:04:36,003\r\nC\xf3\u017c, je\u015bli spojrzymy na\nwykres, zobaczymy 100.\r\n\r\n79\r\n00:04:36,003 --> 00:04:38,003\r\nI teraz pytanie, kt\xf3re\nCi zadam, b\u0119d\u0119 mno\u017cy\u0142\r\n\r\n80\r\n00:04:38,003 --> 00:04:41,005\r\nprzez 100, czy b\u0119d\u0119\ndzieli\u0142 przez 100?\r\n\r\n81\r\n00:04:41,005 --> 00:04:42,005\r\nC\xf3\u017c, robimy to samo co wcze\u015bniej.\r\n\r\n82\r\n00:04:42,005 --> 00:04:45,003\r\nZamierzamy z wi\u0119kszej jednostki\nprzej\u015b\u0107 do mniejszej, wi\u0119c jedna\r\n\r\n83\r\n00:04:45,003 --> 00:04:48,002\r\nwi\u0119ksza jednostka jest r\xf3wna\nwielu mniejszym jednostkom.\r\n\r\n84\r\n00:04:48,002 --> 00:04:50,003\r\nWi\u0119c b\u0119dziemy mno\u017cy\u0107.\r\n\r\n85\r\n00:04:50,003 --> 00:04:56,005\r\nWi\u0119c m\xf3wimy, razy 100\ncentymetr\xf3w na metr, tak?\r\n\r\n86\r\n00:04:56,005 --> 00:04:57,003\r\nI to w\u0142a\u015bnie ma sens.\r\n\r\n87\r\n00:04:57,003 --> 00:04:59,006\r\nMamy 100 centymetr\xf3w\nna metr.\r\n\r\n88\r\n00:04:59,006 --> 00:05:02,008\r\nWi\u0119c 50 metr\xf3w razy 100\ncentymetr\xf3w na metr r\xf3wna si\u0119\r\n\r\n89\r\n00:05:02,008 --> 00:05:12,006\r\n50 razy 100 to 5,000, i\npotem metry si\u0119 skracaj\u0105,\r\n\r\n90\r\n00:05:12,006 --> 00:05:15,002\r\ni otrzymujesz centymetry.\r\n'
        
        video_id= "iGzkk7nwWX8F"
        slang = "pl"
        data = {
            "video":video_id,
            "video_language": 'en',
            "language": slang,
            "format": "srt",
            "subtitles": subtitles_string,
            }

        url = "%s?username=admin&password=admin" % reverse("api:0.1:subtitle_handler")
        r = self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        lang = video.subtitle_language(slang)
        self.assertTrue(lang)

        self.assertEquals(90, lang.subtitle_count)
        text =  lang.latest_subtitles()[0].text
        self.assertEquals(text, u'Witam na\nprezentacji o jednostkach.')
        
    def test_subtitle_create2(self):
        subtitles_string = u'1\r\n00:00:01,020 --> 00:00:12,046\r\nAqu\xed tenemos la ecuaci\xf3n 7 por x es igual a 14.\r\n\r\n2\r\n00:00:12,046 --> 00:00:16,019\r\nAntes de intentar resolver esta ecuaci\xf3n vamos a\r\n\r\n3\r\n00:00:16,019 --> 00:00:20,027\r\npensar un poco sobre lo que esto significa.\r\n\r\n4\r\n00:00:20,027 --> 00:00:26,095\r\n7x es igual a 14, es decir 7 por x\r\n\r\n5\r\n00:00:26,095 --> 00:00:34,061\r\n--d\xe9jame escribirlo de esta manera \u2013 7 por x\r\n\r\n6\r\n00:00:34,061 --> 00:00:39,094\r\nescribimos la x en color anaranjado.  7 por x es igual a 14.\r\n\r\n7\r\n00:00:40,076 --> 00:00:43,066\r\nAhora bien, quiz\xe1s te parezca f\xe1cil resolver esta ecuaci\xf3n.\r\n\r\n8\r\n00:00:43,066 --> 00:00:46,013\r\nPodr\xedas pensar en la tabla del n\xfamero 7.\r\n\r\n9\r\n00:00:46,013 --> 00:00:49,000\r\nPor ejemplo, 7 por 1 es igual a 7 entonces la respuesta no es 1.\r\n\r\n10\r\n00:00:49,000 --> 00:00:54,096\r\n7 por 2 es igual a 14, entonces aqu\xed funciona el n\xfamero 2.\r\n\r\n11\r\n00:00:54,096 --> 00:00:56,086\r\nPodr\xedas resolver la ecuaci\xf3n inmediatamente\r\n\r\n12\r\n00:00:56,086 --> 00:00:59,045\r\nintentando con diferentes n\xfameros.\r\n\r\n13\r\n00:00:59,045 --> 00:01:02,011\r\nEntonces tu respuesta en este caso tendr\xeda que ser 2.\r\n\r\n14\r\n00:01:02,011 --> 00:01:03,079\r\nPero lo que queremos hacer es pensar\r\n\r\n15\r\n00:01:03,079 --> 00:01:05,040\r\nen la forma de resolver la ecuaci\xf3n de manera sistem\xe1tica.\r\n\r\n16\r\n00:01:05,040 --> 00:01:07,084\r\nYa veremos que las ecuaciones se vuelven m\xe1s\r\n\r\n17\r\n00:01:07,084 --> 00:01:10,032\r\ny m\xe1s complicadas y no vamos a poder\r\n\r\n18\r\n00:01:10,032 --> 00:01:12,033\r\nresolverlas as\xed no m\xe1s.\r\n\r\n19\r\n00:01:12,033 --> 00:01:14,050\r\nEntonces es muy importante que, primero, entiendas c\xf3mo\r\n\r\n20\r\n00:01:14,050 --> 00:01:16,066\r\nmanipular estas ecuaciones pero es todav\xeda m\xe1s importante que\r\n\r\n21\r\n00:01:16,066 --> 00:01:19,000\r\nentiendas lo que representan las variables.\r\n\r\n22\r\n00:01:19,000 --> 00:01:22,026\r\nEsta ecuaci\xf3n literalmente dice 7 por x es igual a 14.\r\n\r\n23\r\n00:01:22,026 --> 00:01:24,093\r\nEn algebra no escribimos el \u201cpor\u201d.\r\n\r\n24\r\n00:01:24,093 --> 00:01:28,053\r\nCuando escribes dos n\xfameros uno junto al otro, o si escribes un n\xfamero\r\n\r\n25\r\n00:01:28,053 --> 00:01:30,059\r\njunto a un variable, significa que\r\n\r\n26\r\n00:01:30,059 --> 00:01:31,066\r\nest\xe1s multiplicando.\r\n\r\n27\r\n00:01:31,066 --> 00:01:34,058\r\nEs una forma abreviada para anotar las cosas.\r\n\r\n28\r\n00:01:34,058 --> 00:01:37,025\r\nY en general no vamos a utilizar el signo de multiplicaci\xf3n porque\r\n\r\n29\r\n00:01:37,025 --> 00:01:40,093\r\nes muy confuso, dado que la letra x es la variable m\xe1s com\xfan\r\n\r\n30\r\n00:01:40,093 --> 00:01:42,026\r\nen algebra.\r\n\r\n31\r\n00:01:42,026 --> 00:01:49,029\r\nY si yo escribiera 7 por x es igual a 14 y escribo\r\n\r\n32\r\n00:01:49,029 --> 00:01:52,058\r\nel signo de multiplicaci\xf3n como \u201cx\u201d entonces se ver\xeda raro, quedar\xeda\r\n\r\n33\r\n00:01:52,058 --> 00:01:54,083\r\ncomo x-x es decir por-por.\r\n\r\n34\r\n00:01:54,083 --> 00:01:56,066\r\nEntonces en general, cuando se trata de ecuaciones\r\n\r\n35\r\n00:01:56,066 --> 00:01:58,083\r\nespecialmente cuando una de las variables es la letra x,\r\n\r\n36\r\n00:01:58,083 --> 00:02:01,086\r\nno se usa el signo tradicional para la multiplicaci\xf3n.\r\n\r\n37\r\n00:02:01,086 --> 00:02:04,037\r\nPodr\xedas usar otra cosa, por ejemplo un punto para\r\n\r\n38\r\n00:02:04,037 --> 00:02:06,069\r\nrepresentar la multiplicaci\xf3n\r\n\r\n39\r\n00:02:06,069 --> 00:02:10,000\r\nEntonces podr\xedas escribir 7 por x es igual a 14.\r\n\r\n40\r\n00:02:10,000 --> 00:02:12,023\r\nPero no es muy com\xfan.\r\n\r\n41\r\n00:02:12,023 --> 00:02:14,055\r\nSi est\xe1s multiplicando un n\xfamero por un variable\r\n\r\n42\r\n00:02:14,055 --> 00:02:15,093\r\nentonces escribes 7x.\r\n\r\n43\r\n00:02:15,093 --> 00:02:17,093\r\nLiteralmente esto quiere decir 7 por x.\r\n\r\n44\r\n00:02:17,093 --> 00:02:23,015\r\nAhora hay que entender c\xf3mo puedes manipular esta ecuaci\xf3n para\r\n\r\n45\r\n00:02:23,015 --> 00:02:25,063\r\nresolverla.  Vamos a visualizar este concepto.\r\n\r\n46\r\n00:02:25,063 --> 00:02:28,021\r\n7 por x, \xbfqu\xe9 quiere decir?\r\n\r\n47\r\n00:02:28,021 --> 00:02:31,029\r\nVoy a volver a escribir la ecuaci\xf3n\r\n\r\n48\r\n00:02:31,029 --> 00:02:35,028\r\npero la voy a escribir en una forma visual.\r\n\r\n49\r\n00:02:35,028 --> 00:02:37,088\r\nLiteralmente significa que es la cantidad x, sumando a esta misma cantidad 7 veces.\r\n\r\n50\r\n00:02:37,088 --> 00:02:41,007\r\nEsta es la definici\xf3n de la multiplicaci\xf3n.\r\n\r\n51\r\n00:02:41,007 --> 00:02:48,033\r\nLiteralmente es x m\xe1s x m\xe1s x m\xe1s x m\xe1s x \u2013\r\n\r\n52\r\n00:02:48,033 --> 00:02:52,030\r\nson 5 x \u2013 m\xe1s x m\xe1s x.\r\n\r\n53\r\n00:02:52,030 --> 00:02:55,006\r\nAqu\xed est\xe1 en una forma literal, son 7x.\r\n\r\n54\r\n00:02:55,006 --> 00:02:57,002\r\nEs lo mismo que 7x.\r\n\r\n55\r\n00:02:57,002 --> 00:03:00,093\r\nLo voy a volver a escribir\r\n\r\n56\r\n00:03:00,093 --> 00:03:03,064\r\n7x.\r\n\r\n57\r\n00:03:03,064 --> 00:03:10,094\r\nAhora bien, la ecuaci\xf3n nos dice que 7x es igual a 14.\r\n\r\n58\r\n00:03:11,002 --> 00:03:14,029\r\nEntonces voy a dibujar 14 objetos aqu\xed.\r\n\r\n59\r\n00:03:14,029 --> 00:03:19,073\r\nAqu\xed tengo 1, 2, 3, 4, 5, 6, 7, 8\r\n\r\n60\r\n00:03:19,073 --> 00:03:23,088\r\n9, 10, 11, 12, 13, 14.\r\n\r\n61\r\n00:03:23,088 --> 00:03:27,007\r\nLiteralmente estamos diciendo que 7x es igual a 14 objetos.\r\n\r\n62\r\n00:03:27,007 --> 00:03:29,029\r\nEs lo mismo.\r\n\r\n63\r\n00:03:29,029 --> 00:03:32,047\r\nAhora bien, lo dibujo de esta manera para que\r\n\r\n64\r\n00:03:32,047 --> 00:03:34,093\r\npuedas entender lo que vamos a hacer cuando\r\n\r\n65\r\n00:03:34,093 --> 00:03:38,067\r\ndividamos los dos lados de la ecuaci\xf3n por 7.\r\n\r\n66\r\n00:03:38,067 --> 00:03:40,047\r\nVoy a borrar esta parte.\r\n\r\n67\r\n00:03:46,021 --> 00:03:49,040\r\nVoy a dibujar este \xfaltimo c\xedrculo.\r\n\r\n68\r\n00:03:49,040 --> 00:03:52,029\r\nEn general cuando quieres simplificar la ecuaci\xf3n\r\n\r\n69\r\n00:03:52,029 --> 00:03:55,070\r\nel coeficiente es el n\xfamero que se multiplica por\r\n\r\n70\r\n00:03:55,070 --> 00:03:56,087\r\nla variable.\r\n\r\n71\r\n00:03:56,087 --> 00:03:59,094\r\nExiste un n\xfamero que se multiplica por la variable o podr\xedamos decir\r\n\r\n72\r\n00:03:59,099 --> 00:04:02,004\r\nque es el coeficiente multiplicado por la variable igual a\r\n\r\n73\r\n00:04:02,004 --> 00:04:03,010\r\notra cosa.\r\n\r\n74\r\n00:04:03,010 --> 00:04:04,066\r\nLo que quieres hacer es dividir los dos lados de la ecuaci\xf3n por el\r\n\r\n75\r\n00:04:04,066 --> 00:04:08,085\r\ncoeficiente, en este caso es el n\xfamero 7.\r\n\r\n76\r\n00:04:08,091 --> 00:04:11,086\r\nSi divides los dos lados de la ecuaci\xf3n por 7, \xbfcu\xe1l es el resultado?\r\n\r\n77\r\n00:04:12,002 --> 00:04:16,047\r\n7 por algo dividido por 7 es nada m\xe1s\r\n\r\n78\r\n00:04:16,047 --> 00:04:18,048\r\nla cantidad original.\r\n\r\n79\r\n00:04:18,048 --> 00:04:22,068\r\nLos 7 se eliminan uno al otro y 14 entre 7 son 2.\r\n\r\n80\r\n00:04:22,068 --> 00:04:26,039\r\nEntonces la soluci\xf3n va a ser x es igual a 2.\r\n\r\n81\r\n00:04:26,039 --> 00:04:29,037\r\nPero para entenderlo mejor,\r\n\r\n82\r\n00:04:29,037 --> 00:04:33,003\r\nlo que est\xe1 pasando es que estamos dividiendo ambos lados de\r\n\r\n83\r\n00:04:33,003 --> 00:04:36,061\r\nla ecuaci\xf3n por 7, literalmente dividiendo ambos lados por 7.\r\n\r\n84\r\n00:04:36,061 --> 00:04:37,070\r\nEs una ecuaci\xf3n.\r\n\r\n85\r\n00:04:37,070 --> 00:04:40,026\r\nEs decir que esto es igual a esto.\r\n\r\n86\r\n00:04:40,026 --> 00:04:43,060\r\nLo que hago al lado izquierdo de la ecuaci\xf3n, lo tengo que hacer al lado derecho.\r\n\r\n87\r\n00:04:43,060 --> 00:04:46,027\r\nSi los dos lados son iguales, no puedo hacer una operaci\xf3n\r\n\r\n88\r\n00:04:46,027 --> 00:04:48,080\r\na un solo lado y esperar que sigan siendo iguales.\r\n\r\n89\r\n00:04:48,080 --> 00:04:54,087\r\nEntonces si divido el lado izquierdo por 7 tengo que dividirlo\r\n\r\n90\r\n00:04:54,087 --> 00:04:56,006\r\nen 7 grupos.\r\n\r\n91\r\n00:04:56,006 --> 00:04:58,084\r\nHab\xeda 7 x aqu\xed, hab\xeda uno, dos, tres\r\n\r\n92\r\n00:04:58,084 --> 00:05:02,036\r\ncuatro, cinco, seis, siete.\r\n\r\n93\r\n00:05:02,036 --> 00:05:04,073\r\nEntonces hay uno, dos, tres, cuatro, cinco, seis, siete grupos.\r\n\r\n94\r\n00:05:04,073 --> 00:05:07,038\r\nSi divido este lado de la ecuaci\xf3n en siete grupos tambi\xe9n quiero\r\n\r\n95\r\n00:05:07,038 --> 00:05:10,075\r\ndividir el lado derecho en siete grupos.\r\n\r\n96\r\n00:05:10,075 --> 00:05:16,000\r\nUno, dos, tres, cuatro, cinco, seis, siete.\r\n\r\n97\r\n00:05:16,000 --> 00:05:18,093\r\nSi todo esto es igual a todo esto, entonces cada\r\n\r\n98\r\n00:05:18,093 --> 00:05:23,019\r\nuna de estas siete partes\r\n\r\n99\r\n00:05:23,019 --> 00:05:27,023\r\nson equivalentes.\r\n\r\n100\r\n00:05:27,023 --> 00:05:32,004\r\nEntonces se puede decir que esta parte es igual a esta parte.\r\n\r\n101\r\n00:05:32,004 --> 00:05:35,001\r\nEsta parte es igual a esta parte\u2014son\r\n\r\n102\r\n00:05:35,001 --> 00:05:36,009\r\npartes equivalentes.\r\n\r\n103\r\n00:05:36,009 --> 00:05:37,046\r\nAqu\xed hay siete partes, aqu\xed hay siete partes.\r\n\r\n104\r\n00:05:37,046 --> 00:05:41,060\r\nEntonces cada x tiene que ser igual a dos de estos objetos.\r\n\r\n105\r\n00:05:41,060 --> 00:05:44,086\r\nEn este caso\r\n\r\n106\r\n00:05:44,086 --> 00:05:49,073\r\ndibujamos estos objetos y\r\n\r\n107\r\n00:05:49,073 --> 00:05:51,003\r\nx es igual a 2.\r\n\r\n108\r\n00:05:51,003 --> 00:05:53,053\r\nAhora vamos a hacer un par de ejemplos m\xe1s para que\r\n\r\n109\r\n00:05:53,053 --> 00:05:55,080\r\nte quede claro que estamos hablando de una ecuaci\xf3n\r\n\r\n110\r\n00:05:55,080 --> 00:05:58,037\r\ny que cualquier operaci\xf3n que hagas a un lado de la ecuaci\xf3n\r\n\r\n111\r\n00:05:58,037 --> 00:06:01,055\r\ntienes que hacerla al otro lado.\r\n\r\n112\r\n00:06:05,003 --> 00:06:13,094\r\nAqu\xed tenemos la ecuaci\xf3n 3x es igual a 15.\r\n\r\n113\r\n00:06:13,094 --> 00:06:16,026\r\nUna vez m\xe1s, es posible resolverla sin escribir nada.\r\n\r\n114\r\n00:06:16,026 --> 00:06:19,045\r\nMe dices que esto es 3 veces alg\xfan\r\n\r\n115\r\n00:06:19,045 --> 00:06:20,031\r\nn\xfamero que es igual a 15.\r\n\r\n116\r\n00:06:20,031 --> 00:06:22,069\r\nPodr\xedas revisar la tabla del n\xfamero 3 e identificar la respuesta.\r\n\r\n117\r\n00:06:22,069 --> 00:06:24,093\r\nPero si quieres resolverla en una forma sistem\xe1tica,\r\n\r\n118\r\n00:06:24,093 --> 00:06:27,013\r\ny es bueno entenderla sistem\xe1ticamente, entonces . . .\r\n\r\n119\r\n00:06:27,013 --> 00:06:30,034\r\nlo que est\xe1 al lado izquierdo es igual a lo que est\xe1 al lado derecho.\r\n\r\n120\r\n00:06:30,034 --> 00:06:32,033\r\n\xbfQu\xe9 tengo que hacer al lado izquierdo\r\n\r\n121\r\n00:06:32,033 --> 00:06:34,026\r\npara que quede solamente la x?\r\n\r\n122\r\n00:06:34,026 --> 00:06:37,006\r\nPara tener solamente la x, tengo que dividir por 3.\r\n\r\n123\r\n00:06:37,006 --> 00:06:40,024\r\nY queremos hacer esto porque si tenemos 3 veces\r\n\r\n124\r\n00:06:40,024 --> 00:06:43,067\r\nalg\xfan n\xfamero y dividimos por 3, los 3 se eliminan\r\n\r\n125\r\n00:06:43,067 --> 00:06:45,008\r\ny me quedo solamente con la x.\r\n\r\n126\r\n00:06:45,008 --> 00:06:48,016\r\nAhora bien, 3x es igual a 15.\r\n\r\n127\r\n00:06:48,016 --> 00:06:52,033\r\nEntonces si divido el lado izquierdo por tres, para mantener\r\n\r\n128\r\n00:06:52,033 --> 00:06:57,060\r\nla ecuaci\xf3n tambi\xe9n tendr\xeda que dividir el lado derecho por tres.\r\n\r\n129\r\n00:06:57,060 --> 00:06:58,092\r\n\xbfQu\xe9 tenemos?\r\n\r\n130\r\n00:06:58,092 --> 00:07:00,007\r\nAl lado izquierdo tenemos\r\n\r\n131\r\n00:07:00,007 --> 00:07:03,081\r\nx, solamente x.\r\n\r\n132\r\n00:07:03,081 --> 00:07:07,083\r\nY al lado derecho, \xbfcu\xe1nto es 15 dividido por tres?\r\n\r\n133\r\n00:07:07,083 --> 00:07:11,025\r\nEs 5.\r\n\r\n134\r\n00:07:11,025 --> 00:07:14,049\r\nPodr\xedas haber resuelto la ecuaci\xf3n de otra manera,\r\n\r\n135\r\n00:07:14,049 --> 00:07:15,082\r\naunque realmente son equivalentes.\r\n\r\n136\r\n00:07:15,082 --> 00:07:20,050\r\nSi empiezo con la ecuaci\xf3n 3x es igual a 15, podr\xedas decir\r\n\r\n137\r\n00:07:20,050 --> 00:07:26,027\r\nque en vez de dividir por tres, podr\xeda quitar este tres y\r\n\r\n138\r\n00:07:26,027 --> 00:07:28,073\r\nquedarme solamente con x si multiplico los dos lados\r\n\r\n139\r\n00:07:28,073 --> 00:07:31,016\r\nde la ecuaci\xf3n por 1/3.\r\n\r\n140\r\n00:07:31,016 --> 00:07:33,006\r\nTambi\xe9n funciona cuando multiplico los dos\r\n\r\n141\r\n00:07:33,006 --> 00:07:36,019\r\nlados de la ecuaci\xf3n por 1/3.\r\n\r\n142\r\n00:07:36,041 --> 00:07:38,073\r\nCuando multiplicas el lado derecho, 1/3 por\r\n\r\n143\r\n00:07:38,073 --> 00:07:46,077\r\n3, es igual a 1, o 1x.\r\n\r\n144\r\n00:07:46,077 --> 00:07:52,084\r\n1x es igual a 15 por 1/3, es igual a 5.\r\n\r\n145\r\n00:07:52,084 --> 00:07:55,001\r\nY 1 por x es lo mismo que x, entonces\r\n\r\n146\r\n00:07:55,001 --> 00:07:58,051\r\nx es igual a 5.\r\n\r\n147\r\n00:07:58,051 --> 00:08:02,008\r\nEstas dos formas de resolver la ecuaci\xf3n son equivalentes.\r\n\r\n148\r\n00:08:02,008 --> 00:08:04,019\r\nSi divides los dos lados por 3, es lo mismo que\r\n\r\n149\r\n00:08:04,019 --> 00:08:11,015\r\nmultiplicar los dos lados de la ecuaci\xf3n por 1/3.\r\n\r\n150\r\n00:08:11,015 --> 00:08:12,074\r\nAhora vamos a resolver otra ecuaci\xf3n, una\r\n\r\n151\r\n00:08:12,074 --> 00:08:14,066\r\nque es un poco m\xe1s complicada.\r\n\r\n152\r\n00:08:14,066 --> 00:08:16,066\r\nY voy a cambiar la variable.\r\n\r\n153\r\n00:08:16,066 --> 00:08:36,080\r\nDigamos que la ecuaci\xf3n es 2y m\xe1s 4y es igual a 18.\r\n\r\n154\r\n00:08:36,080 --> 00:08:38,074\r\nAhora es m\xe1s dif\xedcil resolverla\r\n\r\n155\r\n00:08:38,074 --> 00:08:39,086\r\nas\xed no m\xe1s.\r\n\r\n156\r\n00:08:39,086 --> 00:08:42,031\r\nEstamos diciendo que 2 veces algo, m\xe1s 4 veces este mismo algo\r\n\r\n157\r\n00:08:42,031 --> 00:08:45,066\r\nes igual a 18.\r\n\r\n158\r\n00:08:45,066 --> 00:08:47,080\r\nEsta vez es m\xe1s dif\xedcil pensar as\xed no m\xe1s en el n\xfamero.\r\n\r\n159\r\n00:08:47,080 --> 00:08:48,084\r\nPodr\xedas intentarlo.\r\n\r\n160\r\n00:08:48,084 --> 00:08:52,013\r\nPor ejemplo si \u201cy\u201d fuera igual a 1 ser\xeda 2 por 1 m\xe1s 4 por 1.\r\n\r\n161\r\n00:08:52,013 --> 00:08:53,039\r\nNo funciona.\r\n\r\n162\r\n00:08:53,039 --> 00:08:55,043\r\nEntonces pensamos en c\xf3mo resolverla de manera sistem\xe1tica.\r\n\r\n163\r\n00:08:55,043 --> 00:08:56,086\r\nPodr\xedas seguir adivinando y posiblemente llegar\xedas\r\n\r\n164\r\n00:08:56,086 --> 00:08:59,048\r\na la respuesta, pero veamos c\xf3mo resolverla de manera sistem\xe1tica.\r\n\r\n165\r\n00:08:59,048 --> 00:09:00,073\r\nVamos a visualizar el proceso.\r\n\r\n166\r\n00:09:00,073 --> 00:09:05,006\r\nSi tengo dos \u201cy\u201d \xbfqu\xe9 quiere decir?\r\n\r\n167\r\n00:09:05,006 --> 00:09:08,093\r\nLiteralmente implica que tengo dos \u201cy\u201d, una sumando a la otra.\r\n\r\n168\r\n00:09:08,093 --> 00:09:11,094\r\nY m\xe1s y.\r\n\r\n169\r\n00:09:11,094 --> 00:09:21,037\r\nA esta cantidad voy a sumar cuatro \u201cy\u201d m\xe1s, en t\xe9rminos reales cuatro veces \u201cy\u201d.\r\n\r\n170\r\n00:09:21,050 --> 00:09:25,091\r\nEntonces es \u201cy\u201d m\xe1s \u201cy\u201d m\xe1s \u201cy\u201d m\xe1s \u201cy\u201d.\r\n\r\n171\r\n00:09:25,091 --> 00:09:33,088\r\nY esta ecuaci\xf3n tiene que ser igual a 18.\r\n\r\n172\r\n00:09:33,088 --> 00:09:39,047\r\nEntonces \xbfcu\xe1ntas \u201cy\u201d tengo que tener al lado izquierdo?\r\n\r\n173\r\n00:09:39,047 --> 00:09:40,091\r\n\xbfCu\xe1ntas \u201cy\u201d tengo?\r\n\r\n174\r\n00:09:40,091 --> 00:09:45,079\r\nTengo una, dos, tres, cuatro, cinco, seis \u201cy\u201d.\r\n\r\n175\r\n00:09:45,079 --> 00:09:50,060\r\nSe puede simplificar la ecuaci\xf3n para que diga 6y es igual a 18.\r\n\r\n176\r\n00:09:51,086 --> 00:09:56,055\r\nEsta parte, 2y m\xe1s 4y es igual a 6y.\r\n\r\n177\r\n00:09:56,055 --> 00:10:00,047\r\nEntonces 2y m\xe1s 4y es igual a 6y y esto tiene sentido.\r\n\r\n178\r\n00:10:00,047 --> 00:10:03,050\r\nSi tengo 2 manzanas m\xe1s 4 manzanas, voy a tener\r\n\r\n179\r\n00:10:03,050 --> 00:10:04,057\r\n6 manzanas.\r\n\r\n180\r\n00:10:04,057 --> 00:10:07,089\r\nSi tengo 2 \u201cy\u201d m\xe1s 4 \u201cy\u201d entonces voy a tener 6 \u201cy\u201d.\r\n\r\n181\r\n00:10:07,089 --> 00:10:09,093\r\nTodo esto tiene que ser igual a 18.\r\n\r\n182\r\n00:10:12,030 --> 00:10:15,043\r\nAhora, ojal\xe1 podamos entender c\xf3mo resolverla.\r\n\r\n183\r\n00:10:15,043 --> 00:10:17,089\r\nSi tengo 6 veces algo es igual a 18, si divido ambos\r\n\r\n184\r\n00:10:17,089 --> 00:10:22,099\r\nlados de la ecuaci\xf3n por 6, puedo resolver por la variable.\r\n\r\n185\r\n00:10:23,007 --> 00:10:29,023\r\nEntonces divido el lado izquierdo por 6 y divido el\r\n\r\n186\r\n00:10:29,026 --> 00:10:32,042\r\nlado derecho por 6.\r\n\r\n187\r\n00:10:32,042 --> 00:10:39,011\r\nY nos quedamos con \u201cy\u201d igual a 3.\r\n\r\n188\r\n00:10:39,011 --> 00:10:40,081\r\nPuedes utilizar el n\xfamero para verificar.\r\n\r\n189\r\n00:10:40,081 --> 00:10:42,004\r\nEs la parte bonita de la ecuaci\xf3n.\r\n\r\n190\r\n00:10:42,004 --> 00:10:44,073\r\nSiempre puedes verificar para saber si te sali\xf3 bien la respuesta.\r\n\r\n191\r\n00:10:44,073 --> 00:10:45,090\r\nVamos a ver si funciona.\r\n\r\n192\r\n00:10:45,090 --> 00:10:51,089\r\n\xbf2 por 3 m\xe1s 4 por 3 es igual a qu\xe9?\r\n\r\n193\r\n00:10:51,089 --> 00:10:56,039\r\n2 por 3 es igual a 6.\r\n\r\n194\r\n00:10:56,039 --> 00:10:59,061\r\nY luego 4 por 3 es igual a 12.\r\n\r\n195\r\n00:10:59,061 --> 00:11:03,045\r\n6 m\xe1s 12 es, de hecho, igual a 18.\r\n\r\n196\r\n00:11:03,045 --> 99:59:59,000\r\nEntonces nos funcion\xf3.\r\n'
        
        video_id= "iGzkk7nwWX8F"
        slang = "es"
        data = {
            "video":video_id,
            "video_language": 'en',
            "language": slang,
            "format": "srt",
            "subtitles": subtitles_string,
            }

        url = "%s?username=admin&password=admin" % reverse("api:0.1:subtitle_handler")
        r = self.client.post(url, data=data)
        video = Video.objects.get(video_id=video_id)
        lang = video.subtitle_language(slang)
        self.assertTrue(lang)

        self.assertEquals(196, lang.subtitle_count)
        text =  lang.latest_subtitles()[0].text
        self.assertEquals(text, u'Aqu\xed tenemos la ecuaci\xf3n 7 por x es igual a 14.')        
