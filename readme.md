![Tests](https://github.com/uwidcit/flaskmvc/actions/workflows/dev.yml/badge.svg)

# About the Internship App
This App allows students to apply for internship opportunities and have Staff members add students to an internship shortlist, where employers can decide to accept or reject them from the opportunity. It is implemented with Flask and exposes mainly a command-line interface for most tasks, and a minor API view

### Key Capabilities

* Student Application: Students can apply for an internship position
* Student Shortlist viewing: Students can view shortlisted positions, and employer responses
* Staff: Adds student to the internship position shortlist
* Employer: Creates an internship position
* Employer: Accpets/Denies a student the internship

### Interfaces

* CLI: `flask` commands for all capabilities, as well as testing.

### Intended Users
students, staff & employers of companies that need a simple system to have students apply for internships and accept them efficiently.

# Flask Commands
## Initialization - *run before anything else*
| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask init`| Creates and initializes the database |

---

## App commands

| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask list_users`| Lists all the users in the database |
|`flask list_students`| Lists all the students in the database |
|`flask list_employers`| Lists all the employers in the database |
|`flask list_staff`| Lists all the staff in the database |
|`flask list_positions`| Lists all the positions in the database |
|`flask list_applications`| Lists all the applications in the database |
|`flask list_shortlist`| Lists all the shortlists in the database |
|`flask view_accepted_applications`| Lists all approved applications in the database |
|`flask view_rejected_applications`| Lists all rejected applications in the database |

---

## Student Commands
| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask student create`| Creates a student user with username, password, GPA, and Degree via interactive prompts | *follow on screen prompts* |
|`flask student apply`| Student submits a new application | flask student apply **student_id** | flask student apply *4* |
|`flask student application_status`| Gets the current status of a specific application | flask student applicationStatus **application_id** | flask student applicationStatus *2* |

---

## Staff Commands
| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask staff create`| Creates a staff user with username and password via interactive prompts | *follow on screen prompts* |
|`flask staff shortlist`| Staff shortlists an application to a position, displaying current APPLIED applications and OPEN positions before prompting for IDs | *follow on screen prompts* |

---

## Employer Commands
| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask employer create`| Creats an employer user with username and password via interactive prompts | *follow on screen prompts* |
|`flask employer open_position`| Employer creates an open position | *follow on screen prompts* |
|`flask employer decide`| Employer accepts or rejects an application | *follow on screen prompts* |

---

## Test Commands
| Command | Description | Usage | Example Usage |
|---------|-------------|-------|---------------|
|`flask test all`| Runs all pytest tests |
|`flask test unitcontroller`| Runs all controller tests |
|`flask test unitmodel`| Runs all model tests |
|`flask test integration`| Runs all integration tests |

**Modifying test output**
Place these at the end of the test command to change the output accordingly

* *-v,-vv*: change verbosity of test to provide more details from output
* *-q*: show less testing detail
---

## Database Migration
If changes are made to the models, the database must be 'migrated' to be synced with these new models, then these commands must be executed using `manage.py`

`flask db init`
`flask db migrate`
`flask db upgrade`
`flask db --help`
