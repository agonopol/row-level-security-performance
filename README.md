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

and prefetch:
```bash
prefetch.py --port 54<96|11> 
```

The join strategy uses existing tables to construct a row level security policy.  First we lock down the page_photo table, then create a function that joins on page_user table and a policy that filters using this function.  

Resulting query plan:

- "Seq Scan on page_photo  (cost=0.00..27834.00 rows=33333 width=34) (actual time=8.207..636.322 rows=7 loops=1)"
- "  Filter: can_access_page((page_id)::bigint, (current_setting('app.user_id'::text))::bigint)"
- "  Rows Removed by Filter: 99993"
- "Planning Time: 0.108 ms"
- "Execution Time: 636.426 ms"

The column strategy alters the database schema by creating a new column in the page_photo table called allowed_users, then fills this column by doing the manual join and populating this array, finally the policy just makes sure that the current user is in the 'allowed_users[]' column.

Resulting query plan:

- "Gather  (cost=1000.00..8293.23 rows=11548 width=72) (actual time=2.739..28.300 rows=12 loops=1)"
- "  Workers Planned: 1"
- "  Workers Launched: 1"
- "  ->  Parallel Seq Scan on page_photo  (cost=0.00..6138.43 rows=6793 width=72) (actual time=9.557..21.149 rows=6 loops=2)"
- "        Filter: ((current_setting('app.user_id'::text))::bigint = ANY (allowed_users))"
- "        Rows Removed by Filter: 49994"
- "Planning Time: 0.473 ms"
- "Execution Time: 28.734 ms"

The prefetch strategy creates a function which populates an allowed_user_ids session variable before making the select statement, this is a prior function call that generates the list of allowed pages a user can see, stores this in a varaible and then using this variable for executing the query

Resulting query plan:

- "Bitmap Heap Scan on page_photo  (cost=43.06..80.60 rows=10 width=34) (actual time=0.055..0.154 rows=10 loops=1)"
- "  Recheck Cond: (page_id = ANY ((string_to_array(current_setting('app.allowed_user_ids'::text), ','::text))::integer[]))"
- "  Heap Blocks: exact=10"
* "  ->  Bitmap Index Scan on page_photo_page_id  (cost=0.00..43.06 rows=10 width=0) (actual time=0.036..0.043 rows=10 loops=1)"
- "        Index Cond: (page_id = ANY ((string_to_array(current_setting('app.allowed_user_ids'::text), ','::text))::integer[]))"
- "Planning Time: 0.093 ms"
- "Execution Time: 0.306 ms"

# Results

Average running time per select * from page_photo query after 1000 queries.

| Strategy  | PG 9.6      | PG 11        |
| ----------|:-----------:| ------------:|
| baseline  | 5.81087ms   |  9.41187ms   |
| join      | 651.74537ms |  626.7019ms  |
| column    | 35.21025ms  |  27.58496ms  |
| prefetch  | .72927ms    |  .70205ms    |

