# moodpoll
App for **easy and good decision making**.

<!-- Note: this file contains some comment-markers which enable the reusage of the text-content at sober-arguments.net/about  -->
<!-- marker_1 -->

*Easy* because creating a poll and taking part is fast and self-explaining.

*Good* because it becomes clear, which options raise the most support and which raise the most resistance inside the group. This insight enables wiser decisions and more focused discussions. 

<!-- marker_2 -->

## Challenge

A group of people wants to agree on some question with more than one possible option. Naively, anybody has one or more votes, and the option with the most votes is chosen. However, there are situations when this leads to suboptimal results, e.g. if two similar options "compete" for votes letting a third one win which objectively is not wanted by most people.

## General Solution

In many situations "systemic consenting" (originally in german: ["Systemisches Konsensieren"](https://www.partizipation.at/systemisches-konsensieren.html)) is a better principle. It tries to find the option which raises the least resistance inside the group, and not the one which has the biggest homogeneous subgroup of supporters. Unfortunately it is not yet well known and derserves some explanation. 

## Contribution of the App `moodpoll`

The app enables to create a poll within a few seconds. Just type in some text. Every new line is a new option. Users can then vote by using a range-slider and thus express a differentiated opinion between maximum rejection and maximum approval. The result is also differentiated: rejecting, neutral and supporting votes are displayed separately for each option. This allows the group to apply the decision scheme which fits best for the situation at hand. Having the concrete resistance values available, it is, however, much more intuitive to apply systemic consenting. It is not even necessary to explain it beforehand. It will probably explain itself. Once the method has proven useful, it can be introduced formally much easier.


## Very Simple Example:

Say Alice, Bob and Carl want to agree when they meet. Available options are:

1. Monday
1. Tuesday 

Alice and Bob have preferences for Monday and are indifferent for Tuesday. Carl prefers Tuesday and is not available on Monday.

Counting only positive votes, Monday would win but exclude one Person. However, Tuesday raises the the least resistance. It is OK for everyone.

While in this situation (few voters, few options) "ordinary communication" would perfectly work, such communication can become quite tedious. As time and willingness to communicate constructively are precious resources they should not be wasted.
  
<!-- marker_3 -->


## Current status

The app is currently in *minimum viable product*-state. It should be applicable for the basic use case but obviously is not finished.

Some missing features:

- Graphical visualization of the results
- Sorting options of the results
- Protecting polls against unwanted read/write-access
- Internationalization
  
