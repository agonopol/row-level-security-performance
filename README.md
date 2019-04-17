# row-level-security-performance
Postgres Row Level Security Performance Test 9.6 vs 11

# Setup

To create the two postgres instances:
```bash
make up
```

This sets up two dockers, one running postgres 9.6 on port 5496 and one running postgres 11 on port 5411

To generate the schemas and seed the instances with toy data:
```bash
make seed-db
```

To tear down the two postgres instances to try another experiment:
```bash
make down
```

# Experiments

To run the experiments execute the python code, be sure to tear the databases up and down between various experiments, as the policies can conflict
The strategies being compared are join:
```bash
join.py --port 54<96|11> 
```

and column:
```bash
column.py --port 54<96|11> 
```

The join strategy uses existing tables to construct a row level security policy.  First we lock down the page_photo table, then create a function that joins on page_user table and a policy that filters using this function.  

The column strategy alters the database schema by creating a new column in the page_photo table called allowed_users, then fills this column by doing the manual join and populating this array, finally the policy just makes sure that the current user is in the 'allowed_users[]' column.

# Results

Average running time per select * from page_photo query after 1000 queries.

| Strategy  | PG 9.6      | PG 11        |
| ----------|:-----------:| ------------:|
| baseline  | 5.81087ms   |  9.41187ms   |
| join      | 651.74537ms |  626.7019ms  |
| column    | 35.21025ms  |  27.58496ms  |

