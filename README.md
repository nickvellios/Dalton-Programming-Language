# Dalton Programming Language

Created by Nick Vellios
8/2018

I was freshening up on Python and playing around with string manipulation.
I was testing the performance of manually parsing strings vs using regular
expressions and my curiousity grew and I began building out an interpreter
for this made up language.  Nothing was planned ahead, and the code mostly
reflects that.  It's very hacked together.  But hell, it works.  :)

**TODO:**

Scoped variables
Ability to return from a code block from inside another code block (call function inside of a code block executed from another call function).  Right now there is only one code block return stack offset saved.
Else statement
Maybe: Add support for variable types.  Surprisingly, the lack of types actually ends up being a bigger hassle.  You have to try to pattern the data in each variable prior to every operation and convert it to a format where you can operate on it.

License
----

Unlicense.  For more information, please refer to <http://unlicense.org/>


**Free Software, Hell Yeah!**