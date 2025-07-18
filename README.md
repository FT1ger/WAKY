`WAKY` - Will Ant Kill You

What is `WAKY`?
---------
`WAKY` is an R script (`.r`) or R markdown (`.rmd`) file checker. It only designed for the student who study in data taming in The University of Adelaide. Since students need to follow the **Deliverable Specifications** (DS), otherwise they can only get very few points, and then they can't pass this course. 

To prevent this from happening again, after you finish your work, `WAKY` will automatically check both you R script and R markdown file, and print a report to remind you that will you got killed by a small mistake, just like an elephant got killed by an ant.

What will `WAKY` do?
-----------
- **Check Deliverable Specifications**

**Deliverable Specifications**(DS) is the mainly reason why you lose your mark in this course. For each DS, you will lost 20% of marks. `DS checker` in `WAKY` will check each DS for you code and list where is the mistake.

- **Check commands you use**

You can only use commands, packages from the course, otherwise you will lose you marks for the question. `Commands checker` in `WAKY` will check all the commands you use and compare them with the reminder sheet. 

- **Print the report**

After `WAKY` finished checking, it will print a report of the result. 

How to use WAKY?
----------------
- Install `pyrlint`. (use: `pip install pyrlint`)

- Download `WAKY_token.py` and `better_reminder.csv`.

- Move your `.R` file and `.Rmd` file to the same directory.

- Run `WAKY_token.py`.

- If everything is fine, you will see the generated report `.log` files.

Warning
---------------
- Due to time constraints, better_reminder does not include all functions, but only the functions that appear in modules 1 to 8. If an unknown function appears in the report, please carefully consider whether to use it.

- WAKY cannot help you complete your assignments, it is just a line of defense to protect your assignment score. Please check the report and your own code very carefully. 

- If you find any false positives or omissions, please leave a message in the issue and leave relevant operation information to help us improve WAKY.
