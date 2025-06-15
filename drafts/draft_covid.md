\- Kevin McCabe, Aleksander Psurek

Abstract

In this paper we investigate the formation of locally centralized
exchange markets using agent-based simulation with minimal computational
and institutional complexity. We find that even with very simple models
of agent behavior, centralized market places emerge. Moreover, we
measure social welfare outcomes for different institutional and
environmental arrangements and find that increasing opportunities to
trade, as well as denser environmental conditions, increase social
welfare and lead to market centralization. Finally, we investigate the
effects of changing social preferences, either permanently or
temporarily, and find that preferences for social distancing - analogous
to those imposed during the COVID lockdown measures - lead to severely
diminished social welfare and lead to permanently depressed social
welfare after their subsidence because of path-dependency in local
market formation.

I. Introduction

Since at latest the development of cities as centers of industry and
exchange in the neolithic period, humans have been gathering at
centralized locations to conduct commerce and improve their welfare. As
the city is not a unique aspect of any one civilization or geography, it
is natural to conclude that this system for facilitating welfare is in
some natural way superior to systems without centralized exchange
points. Similarly, even within cities, the development of downtowns or
commercial centers mirrors the same phenomenon on a smaller scale. While
there is a great diversity among the different forms of these particular
systems, the overall pattern remains the same - people gather in some
centralized place, and they tend to stay there once such a central node
has been established.

In this paper, we investigate a set of minimally computationally
intensive agent strategies which lead to a development of centralized
marketplaces from randomly distributed agent allocations on a spatial
grid. We further investigate the centralization and welfare impacts of
agents following these strategies and find that agents aggregate onto
relatively few points with a simple strategy of choosing not to move if
they can continue to trade at their location.

Moreover, we find that introducing agents which have preferences to be
socially distant leads to lower welfare outcomes for all agents and in
aggregate. We find also that even if such preferences are temporary, the
aggregated points which emerge during the period of social distance lead
to permanent desegregation and welfare decreases with such simple agent
strategies, as a result of market location path-dependence.

Our first result, the emergence of centralized market locations from
simple agent strategies and random allocations, mirrors intuitions about
the emergence of centralized markets in modern and historical economies.
Centralized exchange, in the form of cities, has existed since at least
the Neolithic Age (Lampard, 2023). However, while real-world exchange
generally follows some pattern of development involving trust and
eventually contractual relationships, as for instance in Fafchamps,
1998, which documents such an emergence in African manufacturing, our
setting strips away all elements of trust and contracting. Instead the
behavior of our agents is a result of simple rules meant to facilitate
trade, but it similarly results in path-dependent market formation.

Our result similarly contributes, but is apart from, the set of results
and models about city formation from Scott Page in 1998. Specifically,
in his paper Page creates models in which agents have preferences
relating to the distribution of population of other agents, while being
blind to the economic incentives to form centralized nodes. In contrast,
our model hinges on agents making decisions based on a narrow set of
criteria which compel agents to move or not move based only on the
presence of economic incentives in their immediate grid point.
Therefore, agents are blind to population information and any incentives
outside their own grid position.

Additionally, our result pertaining to the effects of temporary
preference changes, be they imposed or genuine, contra but to the
conversation around the economic and social effects of measures such as
the COVID lockdowns. During the height of the lockdown measures and even
while the first batches of vaccines were being distributed, many
predicted that the economy and the society would "bounce back" in a
"V-shaped" recovery, expecting the overall welfare and societal
arrangements to return to pre-pandemic levels (Kammer, 2021; FRED Blog,
2021; Aspachs, 2021). There were, however, some models and papers which
predicted different "letter-shaped" recoveries, such as one by Sharma et
al. from 2021, which were less saccharine in their predictions,
predicting that the economy could be trapped in some bad state.

Similarly, some empirical papers have pointed to significant and
persistent gaps in employment and output relative to pre-lockdown
levels, such as Schotte al. in 2021. Additionally, some studies have
pointed to the fact that such measures have had different effects on
different types of workers and sectors of industry, and that many of
these changes are likely to be long-lasting (Albanesi, 2021; Jaumotte et
al., 2023; Milesi-Ferretti, 2021). While our study does not capture the
effects of heterogeneous agents and production or exchange processes, it
could be extended to discuss these topics.

The rest of this paper is organized as such: section II discusses the
methods of investigation, section III discusses the results, and section
IV concludes.

II\. Methods

The chief method of investigation in this study is an agent-based
simulation of a simplified two-dimensional exchange space within which
buyers and sellers participate in exchange and which they can move
across. The theoretical formulation for the design of the simulation
follows the microeconomic system design first developed in Hurwicz, 1960
and 1973, and elaborated on in Smith, 1982. Specifically, this
formulation conceptualizes a microeconomic system as a set of
interactions between economic actors called agents through a message
space which is curated or curtailed by institutions, all against the
backdrop of a wider economic environment. This study focuses mostly on
the agents themselves and seeks to limit complexity in all other
aspects, as well as within the agents themselves. As such, the following
portion of this paper will explain each of the components of the
microeconomic system as present within our simulation.

ii.a. Environment

The economic environment contains the institutions and the agents which
interact in the microeconomic system and characterizes the broader world
which the agents exist in. In this study, constant will be the number of
agents and the nature of the market as containing one good. Welfare will
also be measured environment-wide, as a percentage of total surplus
realized relative to that theoretically possible under a perfectly
competitive, unitary market. Our main experiments relate to an
environment where there are 20 buyer and 20 seller agents who are
uniformly randomly distributed on a 10x10 rigid square grid. Smaller
scale tests are performed to show the importance of this spatial
arrangement. Agents are allowed to move and trade for 50-100 "weeks"-
where each week is a set of 10 periods of moving followed by trading.
Welfare calculation for these results are also done at the weekly level.

ii.b. Institutions

There are two institutions in this microeconomic system: a bargaining
institution and a travel institution. The bargaining institution allows
agents to interact with each other if they are on the same grid point
and facilitates trade. Trade takes place over several rounds, with the
main results of this paper implanting a rule of 10-round bidding,
however results are presented for the importance of this variable. Trade
proceeds in a manner of take-it-or-leave-it offers each round, with the
institution crossing trades at a random point between viable bids and
asks. There is no institutional memory of exchange or contractual
relationships created by this exchange, except those instantly
completed, so this institution does not create a path-dependence or
centralization.

The travel institution allows agents to interact with the grid in an
effort to change their position on the grid. While it could contain high
level complexities, akin to real-world travel networks, it is very
simple allowing agents to move between any directly adjacent grid
points, including corners, until they reach the bounding boxes of the
environment's grid. Notably, moving costs the agents nothing, except for
the opportunity cost of remaining at their present location. This travel
institution, therefore, is not sufficiently complex to lead to any
path-dependence or centralization.

ii.c. Agents

The results of this study hinge on the different types of agents that
are implemented in the simulation. In an effort to avoid foregone
conclusions, this study develops the complexity of agents one step at a
time and aims to limit the complexity of agents to the minimum required
to replicate the phenomena of market emergence.

ZID: The simplest type of agent implemented is a zero-intelligence
budget-constrained type, named ZID. This type of agent has been shown in
repeated agent based simulation papers to produce remarkably robust
results near-welfare-maximizing results when participating in market
exchange mechanisms, as documented by Gode and Sunder in 1993. This type
of agent is sufficient for efficient exchange at on a centralized market
place, but as it moves entirely randomly on the grid, it is insufficient
for creating an overall efficient outcome.

ZIDP: A natural addition of computation to this agent type is the
selection of the best presented offer, rather than accepting a random
offer, when agents can accept offers from many agents they will prefer
to accept the offer with the highest price (bid) or lowest price (ask)
depending on their type. This type of trader is termed ZIDP. While this
type of trader will lead to an even more efficient result for
centralized exchanges than the ZID trader, it too will not lead to
market emergence, as it moves randomly.

ZIDA: To incorporate a movement strategy, the ZID agent is augmented
with a preference to stay at a grid point if it is able to contract for
trades. If it is not able to contract for a trade, it will instead
choose to move away. Therefore, agents will move randomly until they
find a grid point with a counterpart agent which may be willing to trade
with them. This type of agent is sufficient to lead to the development
of centralized markets, without the need for complex institutions.

ZIDPA: This agent type incorporates the movement and acceptance of best
offers behavior of the ZIDP and ZIDA agent types. While it is slightly
more complex than the ZIDA agent, it is more realistic that individuals
would accept the best offer they are presented with as it has nearly no
cost.

ZIDPR: This agent type behaves identically to the ZIDPA agent type, with
the exception that it will move away from any grid point on which there
are more than two total agents. Therefore, in an environment consisting
of only ZIDPR agents, the maximum occupancy of a grid point would be
two.

There are, of course, limitations to the way in which these agents are
designed and in their decision making process. While the markets and
path-dependence in this context are emergent, the strategies followed by
the agents are designed, and in particulate the movement choices of ZIDA
and ZIDPR agents depend on lexicographic preferences.

Figure 1 documents the message space through which agents interact with
institutions and the environment. This sequence diagram demonstrates the
basic process which each simulation ran with this microeconomic system
operates.

III\. Experiments and Results

We conduct three types of experiments with the microeconomic system
described above. We first investigate the effects of having each
individual type of agent homogeneously dispersed within the system, and
observe the emergent behavior of these agents based on the described
strategies. We then investigate the effects of mixing the ZIDAP (most
optimal) and ZIDAR (socially-distant) types in different proportions in
an effort to investigate potential effects in long-run preference
changes for even portions of the population as a result of COVID or
similar events. Finally, we investigate the effects of short-term
changes in preferences or policy, switching out portions of the ZIDAP
population with ZIDAR agents for several weeks after a steady state has
been reached with the initial population.

iii.a. Validation of Microeconomic
System![Group](media/image1.png){width="4.714033245844269in"
height="6.500001093613299in"}

Before conducting experiments in this context, we first validate the
microeconomic system variables which will be used for the full-scale
experiments. In figure 2, we present the price and quantity of exchanged
goods, along with the ordered supply and demand, for an environment
which is a 1x1 grid, and thus is fully centralized. These results are
generated with just ZID, zero-intelligence, traders, mimicking the
results from Gode and Sunder, 1993, with traders converging towards the
theoretical price and volume. In figure 3, we demonstrate the effect of
the rounds of bargaining permitted, with efficiency reaching a steady
state by approximately 10 rounds permitted. These results validate the
basic agent bargaining logic and the choice of 10 bargaining rounds.

![Group](media/image1.tif){width="6.058727034120735in"
height="4.62222331583552in"}

![Group](media/image2.tif){width="6.5in" height="5.113800306211724in"}
Similarly, figure 4 investigates the effect of changing the grid size,
while only allowing one movement phase. As expected, the efficiency
collapses as agents are allocated more sparsely on a larger grid.
However, when traders were allowed to move more times by increasing the
number of periods, efficiency improved and reached a steady state by
around the 50 period mark. Because we want to see an emergent market,
these results validate our choice of using a 10x10 grid size and of
having many movement and exchange periods.

![Group](media/image3.tif){width="6.5in" height="5.113800306211724in"}

![Group](media/image4.tif){width="6.5in" height="5.113800306211724in"}

iii.b. Comparative Performance of Agent Types

Our first set of experiments is to uniformly randomly place agents of
each type on the grid and allow them to move and trade for 50 weeks. In
this experiment, we are comparing the efficiency of each trader type to
each other, as well as observing the emergence of steady-state points
for types which converge to some such point. Figure 6 documents the
results of such a comparison. All types except the ZIDP and ZID types
reach a steady state outcome, with ZIDPA types consistently outperform
all other types in a steady state. Notably, however, this result also
holds true for ZIDA types being superior to other types in the steady
state. The ZIDPR type also reaches a steady state, but it plateaus at a
lower level than do the other ZIDA-derivatives.

Figure 7 plots the emergence of efficiency with the ZIDA type along with
the number of grid points which are occupied at a given point in time.
As can be seen in this graph, the efficiency increases while the grid
points occupied decrease. As the number of agents has not changed, the
gird points are more densely occupied and this concentration of agents
is facilitating more efficient exchanges. A centralized market has
therefore emerged.![Group](media/image5.tif){width="6.5in"
height="6.478548775153106in"}

![Group](media/image6.tif){width="6.5in" height="5.235531496062992in"}

iii.c. Mixing-in Socially-Distant Types

Our second set of experiments investigates the result of mixing a
proportion of socially-distant, ZIDPR, agents with the most-optimal
agents, ZIDPA. This experiment seeks to investigate the effects of
heterogeneous types, specifically keeping in mind the different ways
individuals may respond to pressures such as infectious diseases or
which may have to do with preferences against density. Figure 8 puts
this experiment into context by comparing the efficiency results of a
50-50 mixed group with those of homogenous types. Notably, the
heterogenous environment produces results much closer that with 100%
ZIDPR agents, pointing to the large externalities that social distancing
can have on exchange even between other types of agents.

Figure 9 further investigates this phenomenon by plotting the terminal
efficiency of environments with an increasing proportion of ZIDPR agents
in relation to ZIDPA agents. The slope of the regression line is -2.106,
implying that for every additional ZIDPR agent in an environment, the
efficiency will decrease by 2.1. The variance, however, is quite
large.![Group](media/image2.png){width="6.5in"
height="5.179074803149606in"}

![Group](media/image7.tif){width="5.111112204724409in"
height="3.4444444444444446in"}

iii.d. Short-term Preference Changes

Our final set of experiments looks at the effects of changing the
composition of agents in a system which has already reached a steady
state for a short period of time, four weeks, and then reverting the
composition of agents to its original proportions. The agents will
therefore not be randomly allocated at the end of the treatment period,
but will instead be continuing to occupy the spaces which their
predecessors occupied. As can be seen in figure 10, the initial
replacement of ZIDPA with ZIDPR agents results in a precipitous drop of
efficiency, mimicking the expected and real effect of COVID-era
lockdowns. However, once the treatment period is over, the system begins
to recover quickly but does not reach its original efficiency. Instead
it reaches a steady-state plateau below the efficiency which it was
originally at. As can be seen in the figure, even if only 30% of agents
are replaced, representing a restrained response, the same qualitative
results are obtained, though with less outcome variance.

![Image Gallery](media/image3.png){width="6.230723972003499in"
height="2.6935772090988626in"}

IV\. Conclusion

Our study demonstrates the potential for markets to emerge spontaneously
from an environment with uniformly allocated agents with simple
cognition rules and using simple institutions. We demonstrate the
efficiency of such markets and compare its efficiency favorably with
fully decentralized exchange. Moreover, our model sheds light on the
externality effects of social distancing and on the lack of a true
v-shaped recovery following the COVID pandemic lockdowns. The
path-dependence of markets is an understudied and underappreciated
topic, and this paper helps to bring light to these questions.

Further research is required, especially in the area of the
institutional aspects of market formation, as well as the questions of
escaping this local equilibrium trap. Turning to the literature of
institutional development and Schumpeterian destruction appears
necessary to fully understand the complexity of real markets and the
ways in which they space such local optima.

References

Lampard, E. Edwin (2023). city. Encyclopedia Britannica.
https://www.britannica.com/topic/city

Fafchamps, Marcel. (1998). "Market Emergence, Trust, and Reputation,"
Working Papers 96016, Stanford University, Department of Economics.

Hammer, Alfred. (2021). "From Vaccines to V-Shaped Recovery in Europe,"
IMF Blog, IMF.

FRED Blog. (2021). "A V-shaped recovery," FRED.

Sharma, Dhruv, Jean-Philippe Bouchaud, Stanislao Gualdi, Marco Tarzia,
and Francesco Zamponi. (2021). "V--, U--, L-- or W--shaped economic
recovery after Covid-19: Insights from an Agent Based Model," *PLoS
One*, 16(3): e0247823.

Schotte, Simone, Michael Danquah, Robert Darko Osei, and Kunal Sen.
(2021). "The Labour Market Impact of COVID-19 Lockdowns: Evidence from
Ghana," discussion paper series, IZA Institute of Labor Economics, IZA
DP No. 14692

Albanesi, Stefania and Jiyeon Kim. (2021). "Effects of the COVID-19
Recession on the US Labor Market: Occupation, Family, and Gender,"
*journal of Economic Perspectives*, Vol. 35, 3

Jaumotte, Florence, Longji Li, Andrea Medici, Myrto Oikonomou, Carlo
Pizzinelli, Ippei Shibata, Jiaming Soh, and Marina M. Tavares. (2023).
"Digitalization During the COVID-19 Crisis: Implications for
Productivity and Labor Markets in Advanced Economies," Staff Discussion
Notes, International Monetary Fund

Milesi-Ferretti, Gian Maria. (2021). "A most unusual recovery: How the
US rebound from COVID differs from rest of G7," UP FRONT, Brookings
Institute.

Hurwicz, Leonid. (1960). "Optimality and informational Efficiency in
Resource Allocation Processes," in Kenneth Arrow et al., eds.,
Mathematical Methods in the Social Sciences, Stanford: Stanford
University, 27-46.

Hurwicz, Leonid. (1973). "The Design of Mechanisms for Resource
Allocation," *American Economic Review Proceedings*, 63, 1-30.

Smith, Vernon L. (1982). "Microeconomic Systems as an Experimental
Science," *The American Economic Review*, Vol. 72, 5, 923-955.

Gode, Dhananjay K. and Shyam Sunder. (1993). "Allocative Efficiency of
Markets with Zero-Intelligence Traders: Market as a Partial Substitute
for Individual Rationality," *Journal of Political Economy,* Vol. 101,
1, 119-137.
