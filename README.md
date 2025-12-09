# ClimbCoach

ClimbCoach is an AI-powered climbing training assistant that helps users plan workouts, track progress, and analyze training load. It combines a SvelteKit frontend with a Python/FastAPI backend orchestrated by Anthropic's Claude.

## Features

- **AI Coaching**: Chat with a climbing coach to generate personalized workouts and training sessions.
- **Training Load Analysis**: Tracks Acute:Chronic Workload Ratio (ACWR) to prevent overtraining.
- **Exercise Database**: Searchable database of 2900+ climbing-specific exercises.
- **Progress Tracking**: Log climbs and workout completion details.

## Architecture

### Backend & AI Agent

The backend (`backend/`) is built with **FastAPI** and uses **Anthropic's Claude** to power the `ClimbingCoachSystem`.

**Tool Calling Capabilities:**
The AI agent is equipped with specific tools to interact with the application's data:

1.  **`get_training_load`**: Retrieves the user's current training load metrics (Acute Load, Chronic Load, ACWR) to provide data-driven recommendations and prevent injury.
2.  **`search_exercises`**: Searches a comprehensive database of exercises (sourced from Kaggle and Google Sheets) by body part, equipment, or type.
3.  **`lookup_workouts`**: Fetches existing workout templates from the database to link them to new training sessions.
4.  **`create_workout`**: Parses natural language requests (e.g., "Create a finger strength workout for Tuesday") into structured workout plans and saves them to the database.
5.  **`create_training_session`**: Logs completed or scheduled sessions, including specific climbs (grades, attempts) and links them to workouts.

### Database Structure

The application uses **PostgreSQL** with **Prisma** ORM. The schema (`prisma/schema.prisma`) is designed around training sessions and workouts:

-   **`TrainingSession`**: Represents a specific training event (past or future). It is the central hub for logging activity.
    -   Links to a `Workout` (the plan followed).
    -   Contains a list of `Climb`s performed during the session.
-   **`Climb`**: Represents an individual climb (boulder or sport route).
    -   Tracks `grade`, `attempts`, and style flags.
-   **`Workout`**: A reusable template or specific plan consisting of exercises.
    -   Contains multiple `Exercise` records (sets, reps, duration, rest).
    -   Can be scheduled for a specific date.
-   **`Progress`**: Tracks the actual completion of a `Workout` by a `User`.
    -   Contains `ProgressSet`s to log specific weight, reps, and RPE for each exercise.
-   **`User`**: Manages user identity and links to their progress history.

## Development

### Frontend (SvelteKit)

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

#### Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npx sv create

# create a new project in my-app
npx sv create my-app
```

#### Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

#### Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
