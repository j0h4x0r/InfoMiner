# InfoMiner

Extract association rules from NYC Open Data Site

## Data Description

### Which NYC Open Data data set(s) we used to generate the INTEGRATED-DATASET file?

We used [Condominium Comparable Rental Income - Manhattan - FY 2009/2010](https://data.cityofnewyork.us/Housing-Development/DOF-Condominium-Comparable-Rental-Income-Manhattan/ad4c-mphb) dataset.

### What (high-level) procedure we used to map the original NYC Open Data data set(s) into our INTEGRATED-DATASET file?

1. Remove uninteresting attributes.

Not all the attributes in the dataset are interesting. The attributes we *retained* in the dataset are:
(Attribute name starting with) MANHATTAN CONDOMINIUM PROPERTY: Boro-Block-Lot, Neighborhood, Building Classification, Total Units, Year Built, Gross SqFt, Est. Gross Income, Gross Income per SqFt, Full Market Value, Market Value per SqFt

2. Change of the attribute Boro-Block-Lot

We only retained the block number in this attribute. For example, if a Boro-Block-Lot value is 1-00007-7501, we will only keep the value 00007.

3. Rename the attributes

For simplicity, we remove the prefix "MANHATTAN CONDOMINIUM PROPERTY" from all the attribute names, and then remove spaces in the attribute names. We also rename "Boro-Block-Lot" to "Block". The final attribute names in our integrated data are:
Block, Neighborhood, BuildingClassification, TotalUnits, YearBuilt, GrossSqFt, EstGrossIncome, GrossIncomePerSqFt, FullMarketValue, MarketValuePerSqFt

### What makes our choice of INTEGRATED-DATASET file interesting?

1. Why the dataset we selected is interesting?

The dataset is about the estimated rental income and market value of Manhattan condominiums. It also contains some basic information including address, classification, etc. of the condominiums. Thus we can find many meaningful patterns from this dataset. The dataset contains more than 1000 properties, covering all areas in Manhattan. So the information we find will be strongly supported.

2. Why some attributes are not interesting?

Attributes related to "comparable rental" are the statistics of similar rental properties that are used to value the condominium. While this part of the data is important for the evaluation, it is not interesting in our scenario here because these properties have similar physical features and location to the corresponding condominiums.

Since all the properties in the data are in Manhattan, the Boro number is always 1. And if we keep Lot number, then the "Block-Lot" is unique for each row. Thus only keeping Block number is enough.

Condo Section and Address are unique for each row, so their support will be very low when finding association rules. Thus it is meaningless to retain them. For address, if we just keep the street name, it will be similar to the block number, so it is sufficient to just keep the block number to indicate the address information.

3. What information can we expect to find from the data we extracted?

The attributes we select in our data including address information(block, neighborhood), building information(building classification, total units, year built, gross square feet) and value(gross income, market value). So potential information we may care about includes the relation between position and value, how the value varies for different building types, etc. We may also find the most frequent building type(s) in some areas.

## How to run?

Run the following command:
```
python main.py <INTEGRATED-DATASET> <min_sup> <min_conf>
```
The parameters are:
* <INTEGRATED-DATASET> - the path of the integrated dataset CSV file
* <min_sup> - the value of minimum support
* <min_conf> - the value of minimum confidence

## System Design

### Code Architecture

We have designed our system as a class called `AprioriExtractor`. The class can be instantiated given the following three parameters: `datafile` (name of the .csv file), `min_sup` and `min_conf` as the minimun support and confidence taken from command line input. There are two more vairables in the AprioriExtractor class: `discrete_granularity` and `discrete_start`, this will be discussed in the 'discretize numeric arribute' section.

Our main function calls for the `run()` function, which does the following steps:
* read data from file: `loadData()` function reads data and headers from the .csv file
* sort items in transactions: keep each transaction in sorted order for later generation of new frequent items
* a priori Algorithm implemented exactly following the Agrawal and Srikant paper:
  * compute large 1-itemsets: candidate generation for 1-itemset and then use selectCandidates() to comput L_1
  * compute large k-itemsets: while L_(k-1) is not empty, we continue to compute the candidates by calling the function `apriorGen()`, and then use `selectCandidates()` to filter out the L_k with support and confidence above threshold.
* extract rules from large itemsets: call function `extract1RRules()` to extract association rules with exactly one item on the right hand side and with at least one item on the left hand side.

### Algorithms

Detailed description for each step (The definitions for L_k and C_k are the same as the [paper](http://www.cs.columbia.edu/~gravano/Qual/Papers/agrawal94.pdf)):

1. Read data from file&discretize numeric arribute

  - First we load the .csv file into a list called database, and name of attribute into a list called header. 
  - In order to discretize the numeric fields such as 'market value' and 'estimated gross income', for better rule extraction results, we wrote a function discretizeAttribute() which takes in the database and header to set each numeric field values to the top value of the range it falls in.
  - discretizeAttribute() function take the following steps in particular:
    * reads in the discrete_granularity value for current column. If it's below zero it means the field is non-numeric and we dont need to do discretization
    * If current column is numeric, we have precomputed the discrete_start list and set each value to be the minimun value of that column among all transactions, discrete_granularity to be the approperiate stepsize/range of each column.
    * We then set the value in each transaction to whichever upper bound of the range it falls into. The exact function we used are: `((current value) - discrete_start_value of current column) / discrete_granularity_value of current value + 1) * discrete_granularity + discrete_start`
  - sort items in transactions to keep each transaction in sorted order for later generation of new frequent items
  - In the end of this step, we have a database that consists of original non-numeric values and discretized numeric values that are ready for doing A priori algorithm on.

2. A priori algorithm implementation

  - compute large 1-itemsets: candidate generation for 1-itemset and then use `selectCandidates()` to compute L_1
    * the first candidate sets consist of 1-item is simply the union set of all items in our 'market basket'. We use a list of tuples data structure to store all candidates, eg. (5, 5000) represents in column five we have a value of 5000.
    * `selectCandidates()` function takes in the above candidate set and original database, compute the count of support transactions for each candidate, returns a dictionary with the keys large itemsets and the values supports.
  - compute large k-itemsets: while L_(k-1) is not empty, we continue to compute the candidates by calling the function `apriorGen()`, and then use `selectCandidates()` to filter out the L_k with support and confidence above threshold.
    * `apriorGen()` function implements the Apriori Candidate Generation method as described in Section 2.1.1 of the Agrawal and Srikant paper. We joined each candidate set with length k to itself, filter out all itemsets that satisfies the condition mentioned in the in Section 2.1.1 of the Agrawal and Srikant paper, and pruned out itemsets remove candidates whose subsets are not in L_(k-1) before returning the new set of candidates.
    * again we call `selectCandidates()` function, which takes in the above candidate set and original database, compute the count of support transactions for each candidate, returns a dictionary with the keys large itemsets and the values supports.
    * we append the L_(k-1) from the above candidate keys to L set, and continue to generate more candidate sets until there is no more sets.

3. Extract Association Rules

Once we have the large itemsets, to get the rules, we simply iterate through our k sized large itemsets (from k = 2 to the largest one) to generate all  association rules with exactly one item on the right hand side and with at least one item on the left hand side.

More specifically:

`extract1RRules()` function takes in L(large item sets) and Supports(the dictionary with support of each frequent itemsets)
- We first determine if the length of L is bigger than 2, if not it means no rules are extracted
- We know that in a large itemset of size k, the only rules we need to generate are the rules with k-1 items on the LHS and 1 item on the RHS. This is because all rules with < k-1 items on the LHS must have been generated for a smaller k itemset.
- So we simply iterate through L set and generate all combinations with k-1 items on the LHS and append the rules with confidence larger than min_conf
- As discussed in class, given a rule: [LHS] => [RHS], the confidence for this rule is `Support(LHS U RHS)/Support(LHS)`. So we can use precomputed Support dictionary instead of compute the confidence again. This greatly optimizes our program efficiency.

After we stored all selected rules in a list of dictionaries, we simply call our `printdata()` function that writes out the calculated itemsets and rules to the output file in the correct format.

## The command line specification of an interesting sample run

```
python main.py 'INTEGRATED-DATASET.csv'  0.3 0.7
```
Findings:
* When GrossIncomePerSqFt is in the top range [20,40], the BuildingClassification is more likely to be 'R4-ELEVATOR'. 
* Reversely, when the building classification is 'R4-ELEVATOR', and MarketValuePerSqFt is in the top range[150,200], the GrossIncomePerSqFt and GrossSqFt is likely to also be high, which falls in their top range respectively
* YearBuilt in between 1900 and 1950 tends to have GrossIncomePerSqFt in the top range[20,40]

The above findings make sense if we think about it: People with higher income are more likely to live in apartments equipped with elevators, and reversely it also makes sense that wealthy people may live in apartments with less units and have higher market values. It is particularly interesting that apartments built between 1900-1950, maybe during pre-war periods, are attractive to more higher income populations.

## Some significant additional information

### Discretize
This is fully discussed in 'Internal design of the project' section a). We can easily alter the range/start of the numeric fields given a changed dataset by altering the two lists: `discrete_granularity`, `discrete_start`. The current numbers in the tow list are obtained by experiments to make sure we can get meaningful rules with reasonable `min_sup` and `min_conf`.

### Output Clarificaton
The output.txt contains an interesting sample run output, following the format below:
```
==Frequent itemsets (min_sup=30%)
[hearder1: item1], sup
==High-confidence association rules (min_conf=70%)
[header1: item1] => header2: item2  (Conf: 70%, Supp: 30%)
```
