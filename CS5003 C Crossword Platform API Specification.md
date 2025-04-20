
# CS5003 Crossword Platform API Specification v1.0

## 1. Introduction

This document specifies the Application Programming Interface (API) for communication between the CS5003 Crossword client and server. The goal is to define a clear, consistent, and robust protocol for all required application features.

## 2. General Principles

* **Protocol:** Communication occurs over standard TCP/IP sockets.
* **Data Format:** All messages exchanged between client and server MUST be encoded as JSON objects using UTF-8 encoding. Each message (JSON object) should be terminated by a newline character (`\n`) to allow the receiver to delineate messages easily on the stream.
* **Request/Response Model:** The client initiates requests, and the server sends back responses. Each request should generally expect a single response.

## 3. Base Message Structure

### 3.1 Client Request Structure

All requests sent from the client to the server should follow this general JSON structure:

```json
{
  "action": "ACTION_NAME",
  "auth_token": "USER_SESSION_TOKEN_OR_NULL",
  "payload": {
    // Action-specific data goes here
  }
}

```

-   `action` (string, required): Specifies the requested operation (e.g., "login", "get_puzzle_list").
    
-   `auth_token` (string or null, required): The authentication token received after successful login. Should be `null` for the `login` and `register` actions themselves, and included for all other protected actions.
    
-   `payload` (object, required): Contains data specific to the requested action. Can be an empty object `{}` if no data is needed.
    

### 3.2 Server Response Structure

All responses sent from the server to the client should follow this general JSON structure:

```
{
  "status": "success" | "error",
  "message": "Optional descriptive text",
  "data": {
    // Response-specific data goes here on success
    // Optional error details might go here on error
  }
}

```

-   `status` (string, required): Indicates the outcome of the requested action. MUST be either `"success"` or `"error"`.
    
-   `message` (string, optional): A human-readable message describing the outcome or providing error details.
    
-   `data` (object, optional): Contains the data returned by the server on successful execution. Can be omitted or null if no data needs to be returned. May contain structured error details on failure.
    

## 4. Authentication

Authentication is handled via session tokens.

-   **Login Process:**
    
    -   The client initiates authentication using the `login` action, sending the username and password hash (ideally, the client should hash the password before sending, though basic password transmission might be used initially) in the `payload`.
        
    -   The server validates the credentials against the user database.
        
    -   On successful validation, the server generates a cryptographically secure, unique session token (`auth_token`). This token should be associated with the user's session on the server-side (e.g., stored in memory or a session table linked to the user ID). Session expiry should be considered for enhanced security.
        
    -   The server returns the `auth_token` to the client in the `data` field of a successful response.
        
    -   On failure (invalid credentials), the server returns an `error` status and an appropriate message.
        
-   **Token Storage:**
    
    -   The client MUST securely store the received `auth_token` for the duration of the user's session.
        
-   **Authenticated Requests:**
    
    -   For any action requiring authentication (i.e., most actions other than `login` and `register`), the client MUST include the stored `auth_token` in the `auth_token` field of the request JSON.
        
-   **Server Token Validation:**
    
    -   For every request containing an `auth_token`, the server MUST validate it. This involves:
        
        1.  Checking if the token exists and is well-formed.
            
        2.  Verifying that the token corresponds to an active, non-expired user session on the server.
            
        3.  Identifying the user associated with the token for authorization purposes.
            
    -   If the token is invalid, expired, or does not correspond to an active session, the server MUST return an `error` status response (e.g., `{"status": "error", "message": "Invalid or expired session token"}`).
        
-   **Handling Invalid Tokens (Client-Side):**
    
    -   If the client receives an error response indicating an invalid or expired token, it should discard the stored token and prompt the user to log in again.
        
-   **Registration:**
    
    -   A `register` action (detailed in Section 5.1) is required for new users to create accounts. It typically takes a desired username and password hash. On success, the server creates the user record. It may automatically log the user in and return an `auth_token` or require the user to log in separately via the `login` action.
        
-   **Logout (Optional):**
    
    -   A `logout` action can be implemented. The client sends the current `auth_token`. The server invalidates the corresponding session token, making it unusable for future requests. The client should then discard the token.
        

## 5. API Endpoints (Actions)

This section details the specific actions supported by the API.

### 5.1 User Management Actions

#### 5.1.1 `register`

-   **Description:** Creates a new user account.
    
-   **Requires Auth:** No.
    
-   **Request Payload:**
    
    -   `username` (string, required): The desired username for the new account.
        
        -   _Constraints:_ e.g., 3-20 characters, alphanumeric only. Server must validate.
            
    -   `password` (string, required): The user's chosen password.
        
        -   _Note:_ Client should ideally hash the password before sending. Server expects the password (or hash) for storage. Server must validate password complexity (e.g., minimum length).
            
-   **`Success Response (status: "success"):`**
    
    -   `message`: "Registration successful."
        
    -   `data`: `{}` (Or `{"auth_token": "NEW_TOKEN"}` if auto-login is implemented).
        
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Username already taken."
        
    -   `message`: "Invalid username format." (Doesn't meet constraints).
        
    -   `message`: "Password does not meet complexity requirements."
        
    -   `message`: "Registration failed due to a server error."
        

#### 5.1.2 `login`

-   **Description:** Authenticates an existing user and returns a session token.
    
-   **Requires Auth:** No.
    
-   **Request Payload:**
    
    -   `username` (string, required): The user's registered username.
        
    -   `password` (string, required): The user's password (or hash, matching what was stored during registration).
        
-   **`Success Response (status: "success"):`**
    
    -   `message`: "Login successful."
        
    -   `data`:
        
        -   `auth_token` (string): The unique session token for subsequent authenticated requests.
            
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid username or password."
        
    -   `message`: "Login failed due to a server error."
        

#### 5.1.3 `logout` (Optional)

-   **Description:** Invalidates the user's current session token.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:** `{}` (No payload needed, token is in the main request structure).
    
-   **`Success Response (status: "success"):`**
    
    -   `message`: "Logout successful."
        
    -   `data`: `{}`
        
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token." (Standard auth error).
        
    -   `message`: "Logout failed due to a server error."
        

### 5.2 Puzzle Actions

#### 5.2.1 `get_puzzle_list`

-   **Description:** Retrieves a list of available crossword puzzles.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:** `{}`
    
    -   _Future Enhancements:_ Could add optional filters here, e.g., `{"difficulty": "easy", "solved_status": "unsolved"}`.
        
-   **`Success Response (status: "success"):`**
    
    -   `data`:
        
        -   `puzzles` (list): A list of `PuzzleListItemObject` (defined in Section 6). Example: `[{"id": 1, "title": "Beginner Fun", "author": "admin", "difficulty": "easy", "solved_by_user": true}, ...]`
            
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Failed to retrieve puzzle list."
        

#### 5.2.2 `get_puzzle`

-   **Description:** Retrieves the details for a specific puzzle, required for the client to display it for solving. Does **not** include answers.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:**
    
    -   `puzzle_id` (int, required): The unique identifier of the puzzle to retrieve.
        
-   **`Success Response (status: "success"):`**
    
    -   `data`: `PuzzleDetailObject` (defined in Section 6). Contains:
        
        -   `id` (int)
            
        -   `title` (string)
            
        -   `author` (string)
            
        -   `grid_layout` (list of strings): The structure of the grid (e.g., `["..#", ".#.", "#.."]`).
            
        -   `clues` (list of `ClueObjectWithoutAnswer`): List of clues, each including number, direction, row, col, clue text, and word length (defined in Section 6).
            
        -   `user_progress` (list of strings or null): Optional. The user's previously saved state for this puzzle, if resuming. Format matches `grid_layout` but with characters or nulls.
            
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Puzzle not found."
        
    -   `message`: "Failed to retrieve puzzle details."
        

#### 5.2.3 `create_puzzle`

-   **Description:** Allows an authenticated user to submit a new crossword puzzle they created.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:** (Must match the data structure prepared by the client UI)
    
    -   `title` (string, required): The title for the new puzzle.
        
    -   `grid_layout` (list of strings, required): The grid structure (e.g., `["..#", ".#.", "#.."]`). Server MUST validate this layout (e.g., connectivity, dimensions).
        
    -   `clues` (list of `ClueObjectWithAnswer`, required): List of clue definitions, including answers (defined in Section 6). Server MUST validate consistency between clues, answers, and the grid layout.
        
-   **`Success Response (status: "success"):`**
    
    -   `message`: "Puzzle created successfully."
        
    -   `data`:
        
        -   `puzzle_id` (int): The unique identifier assigned to the newly created puzzle by the server.
            
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Invalid puzzle title."
        
    -   `message`: "Invalid grid layout provided." (e.g., format error, invalid characters, disconnected sections).
        
    -   `message`: "Invalid clues data provided." (e.g., answer length mismatch, inconsistent numbering, clues don't fit grid).
        
    -   `message`: "Puzzle creation failed (database error)."
        

#### 5.2.4 `submit_solution`

-   **Description:** Submits a user's completed grid for a specific puzzle to check for correctness and update statistics.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:**
    
    -   `puzzle_id` (int, required): The ID of the puzzle being solved.
        
    -   `solution_grid` (list of strings, required): The user's filled grid. Format should match `grid_layout` but contain the user's letters (e.g., `[["A","B","#"],["C","#","D"],["#","E","F"]]`). Server validates format and dimensions.
        
    -   `time_taken_seconds` (int, optional): Time spent solving, as reported by the client.
        
-   **`Success Response (status: "success"):`**
    
    -   `message`: "Solution processed."
        
    -   `data`:
        
        -   `correct` (boolean): `true` if the submitted solution matches the stored answers exactly, `false` otherwise.
            
        -   `score` (int, optional): A score awarded for solving, if applicable.
            
        -   `stats_updated` (boolean, optional): Indicates if the user's statistics (e.g., puzzles solved count) were updated based on this submission (usually only if `correct` is `true`).
            
        -   `incorrect_cells` (list of [row, col] pairs, optional): If `correct` is `false`, this might contain coordinates of incorrect cells.
            
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Puzzle not found."
        
    -   `message`: "Invalid solution grid format submitted."
        
    -   `message`: "Solution check failed (server error)."
        

_`(Optional: Add an action like save_progress if needed)`_

### 5.3 Statistics Actions

#### 5.3.1 `get_my_stats`

-   **Description:** Retrieves performance statistics for the currently authenticated user.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:** `{}`
    
-   **`Success Response (status: "success"):`**
    
    -   `data`: `UserStatsObject` containing fields like:
        
        -   `username` (string): The user's username.
            
        -   `puzzles_solved` (int): Total number of unique puzzles solved correctly.
            
        -   `puzzles_created` (int): Total number of puzzles created by the user.
            
        -   `average_solve_time_seconds` (float or null, optional): Average time taken for correctly solved puzzles (if tracked). Null if no puzzles solved or time not tracked.
            
        -   `rank` (int or null, optional): User's rank based on a default criterion (e.g., puzzles solved). Null if not ranked.
            
    -   **`Example UserStatsObject:`**
        
        ```
        {
          "username": "user123",
          "puzzles_solved": 15,
          "puzzles_created": 2,
          "average_solve_time_seconds": 345.6,
          "rank": 42
        }
        
        ```
        
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Failed to retrieve user statistics."
        

#### 5.3.2 `get_leaderboard`

-   **Description:** Retrieves a ranked list of users based on specified criteria.
    
-   **Requires Auth:** Yes.
    
-   **Request Payload:** (Optional payload for customization)
    
    -   `ranking_criteria` (string, optional, default: "puzzles_solved"): Criteria for ranking. Examples: "puzzles_solved", "puzzles_created", "average_solve_time". Server determines supported criteria.
        
    -   `limit` (int, optional, default: 10): Maximum number of users to return.
        
-   **`Success Response (status: "success"):`**
    
    -   `data`:
        
        -   `criteria_used` (string): The ranking criteria actually used by the server.
            
        -   `leaderboard` (list): A list of `LeaderboardEntryObject`.
            
    -   **`Example LeaderboardEntryObject:`**
        
        ```
        {
          "rank": 1,
          "username": "crossword_master",
          "value": 152 // Value corresponding to criteria (e.g., puzzles solved)
        }
        
        ```
        
    -   **`Example data:`**
        
        ```
        {
          "criteria_used": "puzzles_solved",
          "leaderboard": [
            {"rank": 1, "username": "crossword_master", "value": 152},
            {"rank": 2, "username": "solver_pro", "value": 148},
            {"rank": 3, "username": "user123", "value": 15}
          ]
        }
        
        ```
        
-   **`Error Responses (status: "error"):`**
    
    -   `message`: "Invalid or expired session token."
        
    -   `message`: "Invalid ranking criteria specified."
        
    -   `message`: "Failed to retrieve leaderboard."
        

### 5.4 Social Actions (If Applicable)

_(Placeholder: e.g., add_friend, list_friends, send_message, get_messages, get_activity_feed)_

## 6. Shared Data Structures

This section defines common data object structures used in the API payloads and responses.

### 6.1 `PuzzleListItemObject`

-   **Description:** Represents a puzzle summary in a list view.
    
-   **Fields:**
    
    -   `id` (int): The unique identifier of the puzzle.
        
    -   `title` (string): The title of the puzzle.
        
    -   `author` (string): The username of the puzzle creator.
        
    -   `difficulty` (string, optional): An indicator of difficulty (e.g., "easy", "medium", "hard").
        
    -   `solved_by_user` (boolean, optional): Indicates if the currently authenticated user has successfully solved this puzzle. Requires server-side logic to determine.
        
-   **Example:**
    
    ```
    {
      "id": 1,
      "title": "Beginner Fun",
      "author": "admin",
      "difficulty": "easy",
      "solved_by_user": true
    }
    
    ```
    

### 6.2 `ClueObjectWithAnswer`

-   **Description:** Represents a single clue definition, including its answer. Used when creating puzzles.
    
-   **Fields:**
    
    -   `number` (int): The clue number displayed on the grid.
        
    -   `direction` (string): The direction of the clue ("A" for Across, "D" for Down).
        
    -   `row` (int): The 0-indexed row number of the clue's starting cell.
        
    -   `col` (int): The 0-indexed column number of the clue's starting cell.
        
    -   `clue` (string): The text of the clue prompt.
        
    -   `answer` (string): The correct answer word for the clue.
        
-   **Example:**
    
    ```
    {
      "number": 1,
      "direction": "A",
      "row": 0,
      "col": 0,
      "clue": "Opposite of black",
      "answer": "WHITE"
    }
    
    ```
    

### 6.3 `ClueObjectWithoutAnswer`

-   **Description:** Represents a single clue definition for display during solving. Excludes the answer but includes the length.
    
-   **Fields:**
    
    -   `number` (int): The clue number displayed on the grid.
        
    -   `direction` (string): The direction of the clue ("A" for Across, "D" for Down).
        
    -   `row` (int): The 0-indexed row number of the clue's starting cell.
        
    -   `col` (int): The 0-indexed column number of the clue's starting cell.
        
    -   `clue` (string): The text of the clue prompt.
        
    -   `length` (int): The number of letters in the correct answer (i.e., the length of the word slot in the grid).
        
-   **Example:**
    
    ```
    {
      "number": 1,
      "direction": "A",
      "row": 0,
      "col": 0,
      "clue": "Opposite of black",
      "length": 5
    }
    
    ```
    

### 6.4 `PuzzleDetailObject`

-   **Description:** Represents the full details of a puzzle needed for the client to display it for solving.
    
-   **Fields:**
    
    -   `id` (int): The unique identifier of the puzzle.
        
    -   `title` (string): The title of the puzzle.
        
    -   `author` (string): The username of the puzzle creator.
        
    -   `grid_layout` (list of strings): The structure of the grid (e.g., `["..#", ".#.", "#.."]`, where '.' is white, '#' is black). Defines the shape and black squares.
        
    -   `clues` (list of `ClueObjectWithoutAnswer`): A list containing all the clues for the puzzle, without answers.
        
    -   `user_progress` (list of strings or null, optional): The user's saved state for this puzzle, if available. Format matches `grid_layout` but contains entered characters or empty strings/nulls for empty cells (e.g., `[["W","H","I","#"],["C","A","",".#."],...]`). `null` if no progress saved.
        
-   **Example:**
    
    ```
    {
      "id": 1,
      "title": "Beginner Fun",
      "author": "admin",
      "grid_layout": [
        ".....#...",
        ".###.#.#.",
        ".#...#...",
        ".......#.",
        ".#####...",
        "...#.#.#.",
        ".#...#...",
        ".#.#.###.",
        "...#....."
      ],
      "clues": [
        {"number": 1, "direction": "A", "row": 0, "col": 0, "clue": "Not difficult", "length": 4},
        {"number": 5, "direction": "A", "row": 0, "col": 6, "clue": "Small insect", "length": 3},
        // ... more clues ...
        {"number": 1, "direction": "D", "row": 0, "col": 0, "clue": "Opposite of stop", "length": 2},
        {"number": 2, "direction": "D", "row": 0, "col": 1, "clue": "Consumed food", "length": 3}
        // ... more clues ...
      ],
      "user_progress": null
    }
    
    ```