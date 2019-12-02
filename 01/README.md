# Day 1: 7110

## Overview

This challenge was a reasonably simple decoding challenge, whereby a number of 
text messages were encoded using an old Nokia 7110 keypad and the resulting
message needed to be derived from that. You are given 3 decoded results so as
to have a jumping off point to find the fourth.

There are a couple of gotcha's to take note of, namely deleting characters, 
moving the cursor left and right, and the amount of time between each button
press.

## Required Software

* python: Used to write the script to decode the message

## Solving the challenge

### Step 1 - Overview

There are three sms.txt files containing decoded messages, and four sms.csv 
files containing two comma-separated numbers. The first takeaway is that
the numbered sms.txt is the output from the numbered csv file. There is also
a keys.h file which contains references to N7110 (similar to the challenge
name) and various keys. There's also a reference to T9 which gives a strong
hint to one of those old mobile phone text options, whereby clicking "3" cycles
through "def3", which is also displayed in the file.

Within the CSV file, the second number likely represents the number clicked on 
the keypad. The first number seems to be a constantly increasing value, which
likely means it's a timestamp of sorts. This can be validated by just looking
at the button presses in sms1.csv and comparing it to sms1.txt.

### Step 2 - Writing a decoder

Given the information we've got, it should be relatively straightforward to 
write a script to decode the final message. We can use the first three messages
to test our output.

#### Time between presses

The first problem to overcome is how to deal with multiple presses cycling 
through the alphabet assuming it's within a time range. To do this, some state 
is required and the time between the current an previous press needs to be
considered. This is achieved by simply referencing the timestamp of the 
previous row each iteration, replacing the timestamp with the difference:

```python
last_timestamp = 0
for t in text:
    if last_timestamp == 0:
        last_timestamp = t[0]
        t[0] = 0
        continue

    timestamp = t[0]
    t[0] = timestamp - last_timestamp
    last_timestamp = timestamp
```

#### Message setup

Once the timestamp issue has been resolved, we need to figure out what time
between presses accounts for a "new" letter as opposed to just cycling through
the alphabet. This can only be achieved by trial and error, although after
looking at the files I started with a value of 500.

The first few presses in each message seem to be 100 (MENU_LEFT), which happens
four times, before keycode 11 (KEYPAD_HASH) is pressed twice. HASH looks to 
select the IME type, so we can assume that IME_ABC is selected, meaning the
text is manually selected rather than using a dictionary. After this initial
setup the text begins to be written, so we can safely ignore it in this case.

#### Cursor

Given the user can either delete a character using a backspace, or simply move
the cursor around the message by selecting left and right, we need a way to 
track where the cursor is in relation to the entered text. These are handled by
keycodes 102 and 103 for left and right respectively, and 101 for deletion.

#### Printing output

A dictionary containing the message as it's being typed is stored, and it's 
much easier to debug as you can see it being typed. For this reason, the 
following snippet uses and underlined character to denote the cursor location, 
as well as handling typed and deleted messages:

```python
printed_message = decoded_message.copy()
printed_message[cursor-1] = '\033[4m' + decoded_message[cursor-1] + '\033[0m'
print(f"{''.join(printed_message)}", end='\r')
sleep(0.1)
```

After the script is run on sms4.csv, a few tweaks can be made where necessary.
I found that the time between keypresses worked best at 1000. The flag is:
```
aotw{l3ts_dr1nk_s0m3_eggn0g_y0u_cr4zy_d33r}
```

The full script is located at [exp.py](exp.py).
