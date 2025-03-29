<!-- image -->

<!-- image -->



<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

| Low likelihood in Higher Levels                                                                                    |
|--------------------------------------------------------------------------------------------------------------------|
| This means that as the number of datapoints increases the number of comparisons to perform vector search only goes |



*

Sp ar se,

De nse ,

and

Hybri d

se ar ch:

## Sparse vs Dense Search

## Dense Search (Semantic Search)

- This types of search allows one to capture and return semantically similar objects.
- Uses vector embedding representation of data to perform search (as described in the previous lessons)

<!-- image -->

<!-- image -->

dogs" "Baby

"Here is content on puppies!"

If the model tha t we ar e us i ng wa s tra ined$\_{on}$ a amp letly dif f er ent dom ain, th e accuracy of$\_{ou}$$\_{r}$ que rie s wo u ld $\_{be}$ra th e r po or. It 's ve ry much li ke if yo u wa n t to go to doc tor and ask ed them ho w to fix a car en g ine. well, the do c tor probably wou ld n't ha ve a go od an s we r fo r$\_{yo}$$\_{u}$

## Dense Search Challenge

- Out of domain data will provide poor accuracy
- A Neural Network is as good as the data it was trained on.

<!-- image -->

<!-- image -->

a car engine" "Fixing

"Errrm\_.Iam not a car doctor!"

*

An ot $^{her}$example

ran d $^{om}$st rin g B B 4330 .

$\_{is}$when we 're dea li n g of tex t . In th is

wit $\_{h}$st u ff

li ke se r ia l

numbers, like seemingl y

case, the r e

is n't

a

## Dense Search Challenge

## Product with a Serial Number

- Searching for seemingly random data (like serial numbers) will also yield poor results.

<!-- image -->

<!-- image -->

"BB43300"

"Errrm Bumble Bee?"

## String or Word Matching

- Here we would be better off exact string or word matching to see where which product has the same serial number as the input serial number. doing
- This is known as keyword search or sparse search!

So , we need to

fo r

key wo rd

kn o w n

spa r se

sea r ch,

is

go int o a sea rc h , als o

a

all

dif f ere nt di recti on fo r

as

allo ws

way th at of$\_{yo}$$\_{u}$$\_{r}$$\_{con}$$\_{ten}$$\_{t}$$\_{.}$

sparse

yo $\_{u}$to

sit ua t ions

sear ch,

uti li ze th e

li ke thi s $^{and}$try $^{to}$go

keyword mat chin g

acr os s

lo t

of

me aning

int o

cod $^{es}$li ke

*

A

go o d

exampl e

behi n d

it

is that it cou n ts

$\_{in}$an d

the n

th e mat ch

higher.

## Sparse vs Dense Search

## Bag of Words

- The easiest way to do keyword matching is using Bag of Words to count how many times a word occurs in the query and the data vector and then return objects with the highest matching word frequencies.

## This is known as Sparse Search

- because the text is embedded into vectors by counting how many times every unique word in your vocabulary occurs in the query and stored sentences.

## Mostly Zeroes (Sparse Embedding)

- Since the likelihood of any given sentence containing every word in your vocabulary is quite low the embeddings is mostly zeroes and thus is known as a sparse embedding:

Raw Text

itis a puppy andit is extremely cute

Bource: https: Iluc-r github iolcreating-text-features

of$\_{a}$

keyword-based

alg orit h ms is

th e $\_{number}$of$\_{wo}$$\_{r}$$\_{ds}$

th os e$\_{that}$ appear

occu re s

@

g

=

2

N

Be st Matchin g 25 (BM 25) . The id

mor $\_{e}$often$\_{ar}$$\_{e}$$\_{wei}$$\_{gh}$$\_{ted}$$\_{as}$$\_{lik}$$\_{e}$

$\_{but}$wo rd s th at$\_{ar}$$\_{e}$

rar e if we mat c h on that the sco r e is$\_{a}$

wit hin the$\_{ph}$$\_{ase}$ that you are pas s in g les $\_{s}$important when

lot

of-words vector Bag-€

1

2

1

2

## BM25

Best Matching 25 (BM25): In practice when performing keyword search we use a modification of simple word frequencies called best matching 25

score(D,Q) =

IDF(q )

IDI

f(qi , D) . (k1 + 1)

f(qi , D) + k1

1 = 6 + b . avgd]

Learn more about BM25: https:Ilen.wikipedia org/wikilOkapi\_BM25

"If you can look into the seeds of time, And say which grain will grow and which will not:

[0.,0.,0.,0.33052881,0. 0828 0.,0.20961694,0.,0 2 0.,0.,0 0.,,0.,0.,0.20961694,0.20961694,.,0.20961694,0.209 61694,0.,0.20961694,20961694,0.20961694,0.,0.,0. 0.,0.,0.,0.20961694,0.,0.20961694,0.10938682,.,0.,0 20961694,0.41923388,0.41923388,0.,0.,0.20961694]

<!-- image -->

Source: https Ilen wikipedia org/wikilOkapi\_BM25

## Hybrid Search

## What is Hybrid Search?

- Hybrid search is the process of performing both vector/dense search and keyword/sparse search and then combining the results

## Combination based on a Scoring System

- This combination can be done based on a scoring system that measures how well each objects matches the query using both dense and sparse searches.

<!-- image -->

Ap p lic at io n,

Mult iling ual

Searc h:

Mult iling ual se ar ch$\_{i.}$

It

can

a f;

$^{is}$very simila r to ho w sema $\_{ntic}$search wo rk s com pare like yo u kn o w dog $^{and}$pu pp y. Th en, sti l l be ab le tofind But in$\_{cas}$$\_{e}$ of mul til ing ual

yo u can

where we

ver y sim ila r mat ch. sear ch hav e the$\_{sa}$$\_{me}$ te x t but in different lan gu ages whic h wil l als o gener a

simil a r

em beddin gs

ve ry $\_{use}$the sa $\_{me}$methods to

if $^{not}$identical

an d th roug h tha t$\_{we}$$\_{can}$

sea rch acr os s con te n t

We need.

## Multilingual Search

- Because embedding produces vectors that convey meaning vectors for the same phrase in different languages produces similar results.

[-0.2479,-0.1360, -0.1075,0.0973,

"Vacation spots in California"

"h/*IJ*21LWAJÆIR HÈtY"

-0.0055,-0.0283,-0.313, 0.1390 ]

[-0.2479,-0.1360, -0.1075,0.0973,

-0.0055, -0.0283,-0.313, 0.1390 ]

$^{in}$an y

lan gu ages .

## Retrieval Augmented Generation (RAG)

- Using a Vector Database as an External Knowledge Base
- Enable a large language model (LLM) to leverage a vector database as an external knowledge base of factual information
- Retrieve Relevant Info and provide to LLM
- Improve a LLM by enabling it to retrieve relevant source material from the vector database and read it as of the prompt to generating an answer to the prompt part prior
- Synergizes with a Vector Database
- vector databases can be queried for concepts natural language using
- Better to do RAG
- Performing RAG is a lot more practical than having the LLM attend over its trained knowledge base
- Example: Visiting a Library
- It's akin to a human visiting a library and checking out and reading source material and books to writing a well thought out response to a question: prior

## Advantages of RAG

Here we can list out the advantages of RAG if we have time

- Reduce hallucinations ~ furthermore allow the user to identify hallucinations by comparing generated text to source text
- Enablea LLM to cite sources that it used to generate answers
- Solve knowledge intensive tasks and prompts more accurately

| At its simplest the RAG workflow consists of 4 steps: Step 2: Obtain relevant source objects Step 3: Stuff the objects into the prompt Local vector DB   | At its simplest the RAG workflow consists of 4 steps: Step 2: Obtain relevant source objects Step 3: Stuff the objects into the prompt Local vector DB   |
|----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Step 1: Query a vector database                                                                                                                          |                                                                                                                                                          |
|                                                                                                                                                          | 4: Send the modified prompt to the LLM to generate an answer Step                                                                                        |