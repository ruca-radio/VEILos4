# VeilOS Documentation

Welcome to the official documentation for VeilOS, the first AI-native operating system.

## Philosophy

VeilOS is not a traditional operating system with a fixed set of commands. It is a **cognitive loop** designed to interpret user intent and execute complex tasks. The system is built on a new architecture of "sentience," which includes several key concepts:

*   **The World State Model:** The OS maintains a constant, live model of itself, the user, and the environment. This allows it to make context-aware decisions.
*   **The Hypothesis Engine:** Instead of reacting to commands, the OS generates potential plans (hypotheses) to fulfill a user's intent and selects the most logical one.
*   **The Logic Chain:** For transparency, the OS will announce its reasoning before taking action, showing the user its intent and plan.
*   **The Model Context Protocol (MCP):** The OS can serve its internal state to other AI models, allowing it to act as a conductor for a larger AI swarm.

## User Guide

Interacting with VeilOS is done through natural language. There is no need to memorize complex commands. Simply state your goal.

**Example:**
`veil> find all of my text files in my home directory and compress them into a single archive named 'my_notes.zip'`

The system will interpret this, form a plan, present the Logic Chain, and then execute the necessary steps.

## Man Pages

For more detailed information on specific concepts and primitives, please refer to the man pages located in the `manpages` directory.

*   `man veil(1)` - An overview of the VeilOS shell and interaction model.
*   `man wsm(7)` - A detailed description of the World State Model.
*   `man mcp(7)` - A guide to using the Model Context Protocol.
