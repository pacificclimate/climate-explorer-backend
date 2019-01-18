# Rule Resolver
Uses [SLY](https://github.com/dabeaz/sly) to process _planners-impacts.csv_.  The output of the module is a dictionary with the truth value of each of the rules in the _planners-impacts.csv_.

Example output:
```
{
    'rule_snow': True,
    'rule_hybrid': True,
    'rule_rain': True,
    'rule_future-snow': False,
    'rule_future-hybrid': True,
    'rule_future-rain': True,
    ...
}
```

### Setup
To run the program create and enter a python3 virtual environment.
```
virtualenv -p python3 venv
source venv/bin/activate
```

Next ensure that you install all the requirements.
```
pip install -r requirements.txt
```

### Run
To run the program pass in a .csv that contains at least the columns _id_ and _condition_.
```
python scripts/main.py --csv tests/planners-impacts-sm.csv --filename tests/test_data.json
```
Please note that the data being used is made up, and not all of the variables in _planners-impacts.csv_ exist in the data file.  Thus you should use _planners-impacts-sm.csv_ or _planners-impacts-test.csv_.


### Program Flow
```
Read planners-impacts.csv and extract id and condition columns (main.py)
| | Input: .csv file
| | Output: dictionary {rule: condition}
|/
Process conditions using SLY into parse trees (resolver.py)
| | Input: string
| | Output: parse tree tuple
|/
Evaluate parse trees to determine truth value of each rule (evaluator.py)
| | Input: parse tree tuple
| | Output: truth value of parse tree (there are some cases where the output of the rule is actually a value)
|/
Print result dictionary {rule: True/False/Value} (main.py)
```

### Testing
Uses [pytest](https://github.com/pytest-dev/pytest).
```
pytest tests/ --cov --flake8 --cov-report term-missing
```
