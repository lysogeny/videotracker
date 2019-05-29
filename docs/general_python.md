Conventions
===========

Some things should probably be kept in mind, as most python codebases adhere to them.

PEP8 is a general python styleguide, that has some best practices in terms of syntax.

Among some things, PEP8 prescibes case for variables, functions, classes and statics.
In short: 

- Use `PascalCase` when defining a class.
- Use `snake_case` when defining functions, methods, or variables.
- Use `UPPER_CASE` when defining static things (although python does not strictly have statics).

Unfortunately, PyQt5 and OpenCV, being wrappers around C++ libraries, don't adhere to this.
Their names are mostly in `camelCase`.

I have still tried to keep most of the codebase here in the PEP8 style.

General python features
=======================

This section explains general features of the python language that are useful to know for understanding this codebase.

General syntax
--------------

Python has Indentation based syntax. What this means, is that, unlike other
languages, you don't denote sections of codes using brackets ({}), but rather
using the level of indentation.

This can cause a couple of problems for newcomers.

For one, in python you can't mix spaces and tabs for indents. You should pick one, and use that.

In this codebase I use spaces.

Function definition
-------------------

Defining functions in python is trivial:

    def fun(x):
        return x * 2

This is a function `fun` that returns it's input multiplied by 2.
Functions are defined by using `def`, then typing the name, enclosing the
parameters in parentheses, and then typing a colon. the function fun can then be used as follows:

    > fun(2)
    4
    > fun(x=3)
    6

In the second example the function was addressed using x as a named argument.
Python has a couple of other function-like constructs that are worth mentioning.
The first of these is the generator.

A generator is a lazier function. While typically you would collect all of the
elements of your list that you want to create, and then return that

    def fun(elements):
	output = []
    	for element in elements:
	    output.append(element * 2)
	return output

The generator introduces a new statement. The `yield`.

    def gen(elements):
        for element in elements:
	    yield element * 2

A function that has been defined this way, does not return a list as an output,
but an iterator. The iterator can be used like a list in some contexts (like a
for loop, comprehension or similar)

    > gen([1, 2, 3, 4, 5])
    <generator object gen at ...>
    > fun([1, 2, 3, 4, 5])
    [2, 4, 6, 8, 10]

Why would you ever want to do this?
One reason may be speed. With a lengthy computation, using generators, and only
lazily calculating what is needed, may give you significant gains.
Another is just plain readability. Arguably the generator is easier to read
than the function.

List, Dict, Tuple and other comprehensions
------------------------------------------

In python, a lot of common uses of for loops can be wrapped into list, dict or other comprehensions.

For instance

    names = ['Alice', 'Bob', 'Charlie']
    capital_names = []
    for name in names:
    	capital_names.append(name.upper())

Can be written as:

    names = ['Alice', 'Bob', 'Charlie']
    capital_names = [name.upper() for name in names]

These can be combined with if conditions to allow for filtering or condition based outputs:

    capital_names = [name.upper() for name in names if len(name) > 3]
    # Gets all names longer than 3 as all upper case.


Docstrings
----------

The codebase makes use of docstrings. Docstrings are strings that are placed as
the first items of a function or class. Ideally they should explain what a
function does. The first row is always a brief one-sentence summary, while
further sections might go into details of the expected behaviour of functions.

A docstring may look like this:

    def add(x, y):
        """Adds x and y

        This functions adds the variables x and y
        """
        return x + y

Type annotations
----------------

Type annotations, also called type hints are a fairly recent feature of the
python language.
They allow the user to document what type of variable a method, function or class should use. 

Currently python does not perform any checking based on these. Only some static code analysis tools make use of them..

An example of type hints:

    def add(x: float, y: float = 2) -> float:
        """Adds x and y"""
        return x + y

In this example x and y are specified as floats. Using the `->` notation, the
function's output is also specified as float.

A hint can use any built in type as a function annotation. More complicated
annotations are possible using the `typing` module. For instance:

    from typing import List

    def flatten(x: List[List]) -> List:
    	"""Returns a flat representation of x
	
	This is an example of a type annotation using types from `typing`.
	The input x is a list of lists. A list is returned.
	"""
	...

Decorators
----------

A decorator is a function (or other callable) that modifies another callable by wrapping a function around it's call.
That may sound complicated, but is a fairly simple thing.
For instance:

    @some_decorator
    def function(x):
	return x*2

is expanded to mean:

    def function(x):
    	return x*2
    function = some_decorator(function)

The decorator `some_decorator` can be something like

    def some_decorator(fun):
	"""Example Decorator that measures the time a function takes and prints the time spent"""
    	def inner_function(*args, **kwargs)
	    # Do something before the function that we decorate is called
	    start_time = time.time()
	    # Call the function
	    result = fun(*args, **kwargs)
	    # Do something after the function that we decorate is called
	    elapsed_time = time.time() - start_time
	    print('Time spent: %f' % elapsed_time)
	    return result
	return inner_function

As you can see, all we need is a function that returns another function, that
does the thing that we want.

Practically, you won't encounter any custom decorators in this codebase, but
there is some decorators from the python language that are used.

### `@property` 

The main decorator that is used in this codebase is the `@property` decorator.
This is a function that can be used to define an attribute for a class that has
a setter and a getter.
Essentially, this is used to avoid the C++-style setter and getter contstructs.

In C++, to increment something, when no `incrementValue` has been defined, you
would do something like this:

    object.setValue(object.value());

Because that is not really readable and python does not have private
attributes, in python you can:

    object.value += 1

To be able to do this, `value` either needs to be a normal attribute or a property defined with `property`.

Using `@property` we can define the python equivalent to the C++ `.value()` and `.setValue()`.

Why would you use this instead of just having `value` be a plain attribute? 
You might want to use this, when setting a value should have other effects
appart from setting the value of the attribute. 
For instance, if we set some attribute of a window, we maybe want to make some
UI elements active.
Additionally, we might want to have a class that represents some kind of a
database, and the values for `value` are not directly stored in the class, but
loaded when `value` is first accessed.

