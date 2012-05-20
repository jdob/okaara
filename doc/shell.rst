Shell
=====

Overview
^^^^^^^^

Let's start with some terminology and basic plumbing.

* A **shell** is a running process that accepts multiple user commands until explicitly exited.
* A shell is made up of one or more **screens**.
* Each screen has its own **menu**.
* The menu is used to let the user make the shell do something.
* A user inputs a menu item's **trigger** to invoke the code tied to that item.
* The shell framework provides hooks to navigate from screen to screen and render the menu.

Getting Started
^^^^^^^^^^^^^^^

The first step is to create the ``Shell`` instance itself. It won't do much until
we populate it, but it has a number of framework methods we'll want access to
for the menu items. The defaults should be sufficient in many cases, however
the ability to pass in a specific ``Prompt`` instance is available as well.

The bulk of the shell is in the screens. Each screen can be thought of as
similar to a web page. The screen's menu is used to do things, such as
functionality or transitioning to another screen.

The common usage is to subclass the ``Screen`` class for each particular screen,
but that's not a hard requirement. The main goal in creating a screen is to add
the appropriate menu items for that screen using the ``add_menu_item`` method.

Menu items are instances of the ``MenuItem`` class and effectively pair the
following pieces:

* The trigger used to invoke the item (e.g. 'q' for quit)
* The item description to show to the user when rendering the menu
* The function to invoke when the item is selected by the user

There are some other things to tweak in a menu item, but those are the basics
and good enough for now.

Keep in mind the ``Shell`` instance has a number of navigational methods that
a screen's menu may want to use. For instance, if a screen should provide the
ability to move to another screen, the shell's ``transition`` method would be
passed to the menu item as its function.

Once the screens are created, they are added to the shell instance. One screen
must be designated as the *home* screen. The home screen is the first screen
displayed to the user. Additionally, the shell has built in menu functions
for navigating directly back to the home screen. The first screen added to the
shell will be designated as the home screen, however this can later be changed
by specifying ``is_home=True`` when adding a different screen.

A sample shell can be found in the samples section of the source code or at:
`<https://github.com/jdob/okaara/blob/master/samples/sample_shell.py>`_
