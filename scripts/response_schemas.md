# NBA API Response Schemas Documentation

This document provides detailed information about the response structures for all endpoints used in the fantasy basketball game.

## Table of Contents

- [Overview](#overview)
- [Schema Files](#schema-files)
- [Field Annotations](#field-annotations)
- [Storage Impact Analysis](#storage-impact-analysis)

## Overview

Each endpoint returns data in a specific format. Understanding these formats is crucial for:

- **Extracting ID fields** for dependency chaining
- **Identifying fantasy-relevant statistics**
- **Optimizing storage costs** by filtering unnecessary fields

All schema files are located in the `scripts/` directory with the naming convention `response_schema_{endpoint}.json`.

---

## Schema Files

### 1. response_schema_scheduleleaguev2.json

**Endpoint**: ScheduleLeagueV2  
**Purpose**: Full NBA season schedule with game results  
**Tier**: 1 (ID Provider)

#### Structure

```
{
  "meta": {...},
  "leagueSchedule": {
    "seasonYear": "2025-26",
    "leagueId": "00",
    "gameDates": [
      {
        "gameDate": "10/22/2025 00:00:00",
        "games": [
          { ...game data... }
        ]
      }
    ]
  }
}
```

#### ID Fields (for chaining)

| Field             | Type   | Used For                  | Location in Response                                 |
| ----------------- | ------ | ------------------------- | ---------------------------------------------------- |
| `gameId`          | string | Future BoxScore endpoints | `leagueSchedule.gameDates[].games[].gameId`          |
| `homeTeam.teamId` | int    | Team identification       | `leagueSchedule.gameDates[].games[].homeTeam.teamId` |
| `awayTeam.teamId` | int    | Team identification       | `leagueSchedule.gameDates[].games[].awayTeam.teamId` |

#### Fantasy-Relevant Fields

| Field                  | Description               | Example Value                    |
| ---------------------- | ------------------------- | -------------------------------- |
| `gameDate`             | Game date                 | "10/22/2025 00:00:00"            |
| `gameDateTimeEst`      | Full datetime EST         | "2025-10-22T19:30:00Z"           |
| `gameStatus`           | Status code               | 3 (1=scheduled, 2=live, 3=final) |
| `gameStatusText`       | Human-readable status     | "Final"                          |
| `homeTeam.teamName`    | Home team name            | "Lakers"                         |
| `homeTeam.teamTricode` | Home team abbreviation    | "LAL"                            |
| `homeTeam.wins`        | Home team wins            | 1                                |
| `homeTeam.losses`      | Home team losses          | 0                                |
| `homeTeam.score`       | Home team score           | 118                              |
| `awayTeam.*`           | Same fields for away team | Similar structure                |
| `arenaName`            | Arena name                | "Crypto.com Arena"               |
| `arenaCity`            | Arena city                | "Los Angeles"                    |

#### Fields to Filter Out

- All broadcaster fields (unless needed): `broadcasters.*`
- Point leaders (redundant): `pointsLeaders`
- Scheduling details: `gameSequence`, `weekNumber`, `weekName`, `gameLabel`, `gameSubLabel`
- Internal fields: `branchLink`, `gameSubtype`, `postponedStatus`

#### Storage Impact

- **Full response**: ~100 fields per game × 1,230 games = 123,000 data points
- **Filtered response**: ~20 fields per game × 1,230 games = 24,600 data points
- **Savings**: 80% reduction

---

### 2. response_schema_playerindex.json

**Endpoint**: PlayerIndex  
**Purpose**: Comprehensive player directory  
**Tier**: 1 (ID Provider)

#### Structure

```
{
  "resource": "playerindex",
  "parameters": {...},
  "resultSets": [
    {
      "name": "PlayerIndex",
      "headers": ["PERSON_ID", "PLAYER_LAST_NAME", ...],
      "rowSet": [
        [2544, "James", "LeBron", ...]
      ]
    }
  ]
}
```

#### ID Fields (for chaining)

| Field       | Type | Used For                                     | Array Index |
| ----------- | ---- | -------------------------------------------- | ----------- |
| `PERSON_ID` | int  | PlayerGameLogs, PlayerNextNGames, Photo URLs | 0           |
| `TEAM_ID`   | int  | Team identification                          | 4           |

#### Fantasy-Relevant Fields

| Header              | Array Index | Description                             | Example Value                  |
| ------------------- | ----------- | --------------------------------------- | ------------------------------ |
| `PERSON_ID`         | 0           | **ID FIELD** - Player identifier        | 2544                           |
| `PLAYER_FIRST_NAME` | 2           | First name                              | "LeBron"                       |
| `PLAYER_LAST_NAME`  | 1           | Last name                               | "James"                        |
| `TEAM_ID`           | 4           | Current team ID                         | 1610612747                     |
| `TEAM_NAME`         | 8           | Team name                               | "Lakers"                       |
| `TEAM_ABBREVIATION` | 9           | Team abbreviation                       | "LAL"                          |
| `JERSEY_NUMBER`     | 10          | Jersey number                           | "23"                           |
| `POSITION`          | 11          | Position                                | "F"                            |
| `HEIGHT`            | 12          | Height                                  | "6-9"                          |
| `WEIGHT`            | 13          | Weight (lbs)                            | "250"                          |
| `COLLEGE`           | 14          | College/HS                              | "St. Vincent-St. Mary HS (OH)" |
| `COUNTRY`           | 15          | Nationality                             | "USA"                          |
| `DRAFT_YEAR`        | 16          | Draft year                              | "2003"                         |
| `DRAFT_ROUND`       | 17          | Draft round                             | "1"                            |
| `DRAFT_NUMBER`      | 18          | Draft pick                              | "1"                            |
| `ROSTER_STATUS`     | 19          | **Availability** (1=active, 0=inactive) | 1                              |
| `FROM_YEAR`         | 24          | First NBA year                          | "2003"                         |
| `TO_YEAR`           | 25          | Current/last year                       | "2025"                         |

#### Fields to Filter Out

- `PLAYER_SLUG` (3) - Redundant URL slug
- `TEAM_SLUG` (5) - Redundant URL slug
- `IS_DEFUNCT` (6) - Internal flag
- `TEAM_CITY` (7) - Available in teams data
- `PTS`, `REB`, `AST` (20, 21, 22) - Use PlayerGameLogs for stats
- `STATS_TIMEFRAME` (23) - Metadata

#### Storage Impact

- **Full response**: 26 fields × 500 players = 13,000 data points
- **Filtered response**: 17 fields × 500 players = 8,500 data points
- **Savings**: 35% reduction

---

### 3. response_schema_playergamelogs.json

**Endpoint**: PlayerGameLogs  
**Purpose**: Complete player game-by-game statistics (PRIMARY STATS SOURCE)  
**Tier**: 2 (Parameterized - requires player_id)

#### Structure

```
{
  "resource": "playergamelogs",
  "parameters": {...},
  "resultSets": [
    {
      "name": "PlayerGameLogs",
      "headers": ["SEASON_YEAR", "PLAYER_ID", "PLAYER_NAME", ...],
      "rowSet": [
        ["2025-26", 2544, "LeBron James", ...]
      ]
    }
  ]
}
```

#### ID Fields (for chaining)

| Header      | Array Index | Used For              |
| ----------- | ----------- | --------------------- |
| `PLAYER_ID` | 1           | Player identification |
| `GAME_ID`   | 6           | Game identification   |
| `TEAM_ID`   | 3           | Team identification   |

#### Fantasy-Relevant Fields (Essential Stats)

| Header              | Array Index | Description                    | Example        |
| ------------------- | ----------- | ------------------------------ | -------------- |
| `SEASON_YEAR`       | 0           | Season                         | "2025-26"      |
| `PLAYER_ID`         | 1           | Player ID                      | 2544           |
| `PLAYER_NAME`       | 2           | Player name                    | "LeBron James" |
| `TEAM_ID`           | 3           | Team ID                        | 1610612747     |
| `TEAM_ABBREVIATION` | 4           | Team abbreviation              | "LAL"          |
| `TEAM_NAME`         | 5           | Team name                      | "Lakers"       |
| `GAME_ID`           | 6           | **ID FIELD** - Game identifier | "0022500001"   |
| `GAME_DATE`         | 7           | Game date                      | "2025-10-22"   |
| `MATCHUP`           | 8           | Matchup description            | "LAL vs. BOS"  |
| `WL`                | 9           | Win/Loss                       | "W"            |
| `MIN`               | 10          | **Minutes played**             | "38:24"        |
| `FGM`               | 11          | **Field goals made**           | 12             |
| `FGA`               | 12          | **Field goals attempted**      | 24             |
| `FG_PCT`            | 13          | Field goal percentage          | 0.5            |
| `FG3M`              | 14          | **3-pointers made**            | 4              |
| `FG3A`              | 15          | **3-pointers attempted**       | 10             |
| `FG3_PCT`           | 16          | 3-point percentage             | 0.4            |
| `FTM`               | 17          | **Free throws made**           | 4              |
| `FTA`               | 18          | **Free throws attempted**      | 6              |
| `FT_PCT`            | 19          | Free throw percentage          | 0.667          |
| `OREB`              | 20          | **Offensive rebounds**         | 2              |
| `DREB`              | 21          | **Defensive rebounds**         | 6              |
| `REB`               | 22          | **Total rebounds**             | 8              |
| `AST`               | 23          | **Assists**                    | 9              |
| `TOV`               | 24          | **Turnovers**                  | 3              |
| `STL`               | 25          | **Steals**                     | 2              |
| `BLK`               | 26          | **Blocks**                     | 1              |
| `BLKA`              | 27          | **Blocks against** (received)  | 0              |
| `PF`                | 28          | **Personal fouls committed**   | 2              |
| `PFD`               | 29          | **Personal fouls drawn**       | 5              |
| `PTS`               | 30          | **Points**                     | 32             |

#### Calculated Fields

- **2-point field goals made**: `FGM - FG3M` (12 - 4 = 8)
- **2-point field goals attempted**: `FGA - FG3A` (24 - 10 = 14)
- **2-point percentage**: `(FGM - FG3M) / (FGA - FG3A)` (8/14 = 0.571)

#### Fields to Filter Out (HUGE SAVINGS)

All ranking fields (indices 35-64):

- `GP_RANK`, `W_RANK`, `L_RANK`, `W_PCT_RANK`
- `MIN_RANK`, `FGM_RANK`, `FGA_RANK`, `FG_PCT_RANK`
- `FG3M_RANK`, `FG3A_RANK`, `FG3_PCT_RANK`
- `FTM_RANK`, `FTA_RANK`, `FT_PCT_RANK`
- `OREB_RANK`, `DREB_RANK`, `REB_RANK`
- `AST_RANK`, `TOV_RANK`, `STL_RANK`, `BLK_RANK`, `BLKA_RANK`
- `PF_RANK`, `PFD_RANK`, `PTS_RANK`
- `PLUS_MINUS_RANK`, `NBA_FANTASY_PTS_RANK`, `DD2_RANK`, `TD3_RANK`

Optional fields to filter:

- `PLUS_MINUS` (31) - Unless needed
- `NBA_FANTASY_PTS` (32) - Can calculate if needed
- `DD2` (33) - Double-double flag (can calculate)
- `TD3` (34) - Triple-double flag (can calculate)

#### Storage Impact (Per Player, 82 Games)

- **Full response**: 65 fields × 82 games = 5,330 data points
- **Filtered response**: 31 fields × 82 games = 2,542 data points
- **Savings**: 52% reduction

**For 500 players**:

- **Full data**: 2,665,000 data points
- **Filtered data**: 1,271,000 data points
- **Total savings**: 52% reduction (~1.4M fewer data points)

---

### 4. response_schema_playernextngames.json

**Endpoint**: PlayerNextNGames  
**Purpose**: Upcoming games for a specific player  
**Tier**: 2 (Parameterized - requires player_id)

#### Structure

```
{
  "resource": "playernextngames",
  "parameters": {...},
  "resultSets": [
    {
      "name": "NextNGames",
      "headers": ["GAME_ID", "GAME_DATE", ...],
      "rowSet": [
        ["0022500045", "2025-10-28", ...]
      ]
    }
  ]
}
```

#### ID Fields (for chaining)

| Header            | Array Index | Used For            |
| ----------------- | ----------- | ------------------- |
| `GAME_ID`         | 0           | Game identification |
| `HOME_TEAM_ID`    | 2           | Home team ID        |
| `VISITOR_TEAM_ID` | 3           | Visitor team ID     |

#### Fantasy-Relevant Fields

| Header                      | Array Index | Description                    | Example              |
| --------------------------- | ----------- | ------------------------------ | -------------------- |
| `GAME_ID`                   | 0           | **ID FIELD** - Game identifier | "0022500045"         |
| `GAME_DATE`                 | 1           | Game date                      | "2025-10-28"         |
| `HOME_TEAM_ID`              | 2           | Home team ID                   | 1610612747           |
| `VISITOR_TEAM_ID`           | 3           | Visitor team ID                | 1610612756           |
| `HOME_TEAM_NAME`            | 4           | Home team full name            | "Los Angeles Lakers" |
| `VISITOR_TEAM_NAME`         | 5           | Visitor team full name         | "Phoenix Suns"       |
| `HOME_TEAM_ABBREVIATION`    | 6           | Home team code                 | "LAL"                |
| `VISITOR_TEAM_ABBREVIATION` | 7           | Visitor team code              | "PHX"                |
| `GAME_TIME`                 | 10          | Game time                      | "19:30"              |
| `HOME_WL`                   | 11          | Home team record               | "3-1"                |
| `VISITOR_WL`                | 12          | Visitor team record            | "2-2"                |

#### Fields to Filter Out

- `HOME_TEAM_NICKNAME` (8) - Redundant
- `VISITOR_TEAM_NICKNAME` (9) - Redundant

#### Storage Impact (5 games per player)

- **Full response**: 13 fields × 5 games = 65 data points per player
- **Filtered response**: 11 fields × 5 games = 55 data points per player
- **Savings**: 15% reduction

**For 500 players**:

- **Full data**: 32,500 data points
- **Filtered data**: 27,500 data points
- **Total savings**: 15% reduction

---

## Field Annotations

### ID Fields Summary

These fields are used to chain dependent endpoints together:

| Endpoint         | Field Name  | Type   | Used In                          |
| ---------------- | ----------- | ------ | -------------------------------- |
| ScheduleLeagueV2 | `gameId`    | string | Future BoxScore endpoints        |
| PlayerIndex      | `PERSON_ID` | int    | PlayerGameLogs, PlayerNextNGames |
| PlayerIndex      | `TEAM_ID`   | int    | TeamInfoCommon                   |
| Teams static     | `id`        | int    | TeamInfoCommon, logo URLs        |
| PlayerGameLogs   | `GAME_ID`   | string | Cross-reference with schedule    |

### Fantasy Stats Fields Summary

All required fantasy game statistics and where to find them:

| Stat Category       | Field(s)                              | Endpoint       |
| ------------------- | ------------------------------------- | -------------- |
| **Points**          | `PTS`                                 | PlayerGameLogs |
| **2-Pointers**      | Calculate: `FGM - FG3M`, `FGA - FG3A` | PlayerGameLogs |
| **3-Pointers**      | `FG3M`, `FG3A`                        | PlayerGameLogs |
| **Free Throws**     | `FTM`, `FTA`                          | PlayerGameLogs |
| **Rebounds**        | `REB`, `OREB`, `DREB`                 | PlayerGameLogs |
| **Assists**         | `AST`                                 | PlayerGameLogs |
| **Steals**          | `STL`                                 | PlayerGameLogs |
| **Turnovers**       | `TOV`                                 | PlayerGameLogs |
| **Blocks**          | `BLK`                                 | PlayerGameLogs |
| **Blocks Against**  | `BLKA`                                | PlayerGameLogs |
| **Fouls Committed** | `PF`                                  | PlayerGameLogs |
| **Fouls Drawn**     | `PFD`                                 | PlayerGameLogs |
| **Minutes**         | `MIN`                                 | PlayerGameLogs |

### Player Info Fields Summary

| Data                   | Field(s)                                | Endpoint          |
| ---------------------- | --------------------------------------- | ----------------- |
| **Name**               | `PLAYER_FIRST_NAME`, `PLAYER_LAST_NAME` | PlayerIndex       |
| **Photo**              | Construct URL from `PERSON_ID`          | PlayerIndex → URL |
| **Position**           | `POSITION`                              | PlayerIndex       |
| **Nationality**        | `COUNTRY`                               | PlayerIndex       |
| **Jersey Number**      | `JERSEY_NUMBER`                         | PlayerIndex       |
| **Height**             | `HEIGHT`                                | PlayerIndex       |
| **Availability**       | `ROSTER_STATUS`                         | PlayerIndex       |
| **Upcoming Opponents** | All fields                              | PlayerNextNGames  |

---

## Storage Impact Analysis

### Overall Savings Summary

| Endpoint                       | Full Size     | Filtered Size | Reduction | Critical?    |
| ------------------------------ | ------------- | ------------- | --------- | ------------ |
| ScheduleLeagueV2               | 123,000 pts   | 24,600 pts    | 80%       | Medium       |
| PlayerIndex                    | 13,000 pts    | 8,500 pts     | 35%       | High         |
| PlayerGameLogs (500 players)   | 2,665,000 pts | 1,271,000 pts | 52%       | **CRITICAL** |
| PlayerNextNGames (500 players) | 32,500 pts    | 27,500 pts    | 15%       | Low          |

**Total Savings**: ~1.5 million data points (~55% overall reduction)

### Cost Impact Example (AWS S3)

Assumptions:

- Storage: $0.023 per GB/month
- Average data point: ~10 bytes (JSON with keys)
- Season: October - April (~6 months)

**Without Filtering**:

- Total data points: ~2.85M
- Storage size: ~28.5 MB
- 6-month cost: ~$0.004 (minimal)

**With Filtering**:

- Total data points: ~1.34M
- Storage size: ~13.4 MB
- 6-month cost: ~$0.002 (minimal)

**Note**: While S3 storage costs are minimal, the primary benefits of filtering are:

1. **Faster data transfer** (reduced bandwidth costs)
2. **Faster processing** (less data to parse)
3. **Better performance** (smaller payloads)
4. **Cleaner data** (only what you need)

### Recommendation: Prioritize PlayerGameLogs Filtering

PlayerGameLogs contains the most redundant data (all ranking fields). Filtering this endpoint provides the biggest impact:

- **1.4M fewer data points**
- **52% size reduction**
- **Faster API responses**
- **Easier data processing**

---

## Usage Examples

### Reading ID Fields

**Extract player IDs from PlayerIndex**:

```python
import json

with open('scripts/response_schema_playerindex.json') as f:
    data = json.load(f)

# Get headers and rows
headers = data['resultSets'][0]['headers']
rows = data['resultSets'][0]['rowSet']

# Find PERSON_ID index
person_id_idx = headers.index('PERSON_ID')
name_idx = headers.index('PLAYER_FIRST_NAME')
last_idx = headers.index('PLAYER_LAST_NAME')

# Extract player IDs and names
players = [
    {
        'id': row[person_id_idx],
        'name': f"{row[name_idx]} {row[last_idx]}"
    }
    for row in rows
]

print(players)
# [{'id': 2544, 'name': 'LeBron James'}, ...]
```

**Extract game IDs from ScheduleLeagueV2**:

```python
with open('scripts/response_schema_scheduleleaguev2.json') as f:
    data = json.load(f)

game_dates = data['leagueSchedule']['gameDates']

game_ids = [
    game['gameId']
    for date_entry in game_dates
    for game in date_entry['games']
]

print(game_ids)
# ['0022500001', '0022500002', ...]
```

### Filtering Fields

**Whitelist approach for PlayerGameLogs**:

```python
ESSENTIAL_FIELDS = [
    'PLAYER_ID', 'PLAYER_NAME', 'GAME_ID', 'GAME_DATE',
    'MIN', 'PTS', 'FGM', 'FGA', 'FG3M', 'FG3A',
    'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK',
    'BLKA', 'TOV', 'PF', 'PFD'
]

def filter_player_game_logs(response_data):
    headers = response_data['resultSets'][0]['headers']
    rows = response_data['resultSets'][0]['rowSet']

    # Find indices of essential fields
    essential_indices = [
        i for i, header in enumerate(headers)
        if header in ESSENTIAL_FIELDS
    ]

    # Filter headers
    filtered_headers = [headers[i] for i in essential_indices]

    # Filter rows
    filtered_rows = [
        [row[i] for i in essential_indices]
        for row in rows
    ]

    return {
        'headers': filtered_headers,
        'rowSet': filtered_rows
    }
```

---

## Next Steps

1. ✅ Review schema files to understand response structures
2. ⏳ Implement field filtering in `fetch_and_upload.py`
3. ⏳ Add `essential_fields` arrays to `endpoints_config.json`
4. ⏳ Test filtering with sample data before full season fetch
5. ⏳ Monitor actual storage usage and adjust filtering as needed
