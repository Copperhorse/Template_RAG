# Answer-level evaluation

149 answerable and 0 unanswerable queries. Rates are Wilson 95% intervals. "Correct" = the answer contains a hand-written key phrase, so it is a lower bound.

## Answerable queries

- gold chunk was in the context the model saw: 84% (125/149; 95% CI 77-89)
- answered (did not refuse): 99% (148/149; 95% CI 96-100)
- answered and cites a chunk that holds the gold snippet: 74% (110/148; 95% CI 67-81)
- answered and contains the expected fact: 0% (0/0; 95% CI 0-0)
- answered and passed every gate: 74% (109/148; 95% CI 66-80)

## Do the gates discriminate?

- correct, among answers that **passed** the gates: 0% (0/0; 95% CI 0-0)
- correct, among answers the gates **flagged**: 0% (0/0; 95% CI 0-0)

## Unanswerable queries (the right behaviour is to refuse)

- refused: 0% (0/0; 95% CI 0-0)
- answered but flagged by the gates: 0% (0/0; 95% CI 0-0)
- answered and passed the gates (the dangerous case): 0% (0/0; 95% CI 0-0)

## If `strict=True` were used (flagged answers become refusals)

- answerable queries answered: 73% (109/149; 95% CI 66-80)
- answerable queries answered correctly: 0% (0/0; 95% CI 0-0)
- unanswerable queries refused: 0% (0/0; 95% CI 0-0)

Mean latency 4.4s per question. Why answers were flagged: {'Unsupported identifier in answer': 15, 'the answer cites no source': 5, 'Unsupported number in answer': 5, 'no verified quote from cited source(s) [2, 4]': 2, 'no verified quote from cited source(s) [3]': 2, 'no verified quote from cited source(s) [3, 4]': 1, 'no verified quote from cited source(s) [2]': 3, 'no verified quote from cited source(s) [1]': 1, 'no verified quote from cited source(s) [4]': 2, 'cites sources that do not exist': 1, 'no verified quote from cited source(s) [5]': 1, 'Unsupported sentence in answer (3 of 5 words not in the sour': 1}

## Per-query record

| id | type | refused | gates | correct | cites gold | answer |
|---|---|---|---|---|---|---|
| s001 | code | no | pass | None | True | A chunk's summary is added to the history if the processing is success |
| s002 | code | no | flag: Unsupported identifier in answer: `text` | None | False | The data structure used to store questions is `QuestionObj`, which has |
| s003 | code | no | pass | None | True | The main application component handling the orchestration of the brows |
| s004 | code | no | pass | None | True | The scoring process is executed in a separate thread because it is 'bl |
| s005 | code | no | flag: Unsupported identifier in answer: `RLock | None | True | The `SharedModel` class manages concurrent access to the underlying mo |
| s006 | code | no | pass | None | True | The code relies on the `tiktoken` library for tokenization and the `la |
| s007 | code | no | pass | None | True | The function extracts numerical values by finding sequences of digits  |
| s008 | code | no | pass | None | True | The overall flow of the method that handles markdown text processing i |
| s009 | doc | no | pass | None | False | When the server fails during the LLM client operation, the system hand |
| s010 | code | no | pass | None | True | The function returns False if the entailment score (p_entail) is great |
| s011 | doc | no | pass | None | True | The system should rotate the logging file instead of truncating it on  |
| s012 | doc | no | pass | None | True | You can retrieve the detailed results, including scores and feedback,  |
| s013 | code | no | flag: the answer cites no source | None | False | When the judge service is unavailable during the verification step, it |
| s014 | doc | no | pass | None | False | The primary function of the component responsible for converting PDF f |
| s015 | code | no | pass | None | True | Liquid AI's D1 decision model (`D1Judge`) was used as an optional judg |
| s016 | doc | no | pass | None | True | Instructions on how to load models can be found in `models.py` [1]. Fo |
| s017 | code | no | flag: Unsupported identifier in answer: `/api/ | None | True | When a user requests the status of a specific session via the endpoint |
| s018 | doc | no | flag: Unsupported number in answer: [2] | None | True | The difficulty level of an interview question is determined in two way |
| s019 | code | no | flag: no verified quote from cited source(s) [ | None | True | The server handles establishing a persistent stream for events using S |
| s020 | code | no | pass | None | True | The detailed results of a single interview session are stored in a dic |
| s021 | doc | no | pass | None | False | To complete a development task, one should do "Step 0" first, then Pha |
| s022 | code | no | pass | None | False | The models initialized in this class constructor are `BAAI/bge-small-e |
| s023 | code | no | flag: the answer cites no source | None | False | The different types of prompt sets available in this system include Pr |
| s024 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The audio processing and stress detection logic is handled by several  |
| s025 | code | no | pass | None | True | If an environment variable is set, the function retrieves it via `env  |
| s026 | code | no | pass | None | True | The system retrieves a user's record without the password hash by exec |
| s027 | code | no | pass | None | True | When the RICH feature is enabled, a `Table` object is created with the |
| s028 | code | no | flag: Unsupported identifier in answer: `Curre | None | True | The system verifies if a specific session belongs to a given user by c |
| s029 | doc | no | pass | None | False | The upcoming development stages are Phase 3 (config + packaging, split |
| s030 | code | no | pass | None | True | If the system encounters an issue with the ffmpeg tool during speech a |
| s031 | doc | no | pass | None | True | User sessions are managed by checking ownership when retrieving a sess |
| s032 | code | no | pass | None | True | The generated question and answer pairs are filtered based on difficul |
| s033 | code | no | pass | None | True | The program handles user input for answering a question by prompting t |
| s034 | doc | no | pass | None | True | The file `data/.jwt_secret` was untracked but not git-ignored, and it  |
| s035 | doc | no | pass | None | False | The main server endpoints and their primary functions include:  *   ** |
| s036 | code | no | pass | None | False | The data fields being prepared for insertion into the database are `ch |
| s037 | code | no | pass | None | False | The file's ownership is verified by checking if the file belongs to th |
| s038 | code | no | pass | None | True | The system ensures that loading all necessary models during startup do |
| s039 | code | no | pass | None | True | The system handles deleting multiple files associated with a specific  |
| s040 | code | no | pass | None | True | The function creates overlapping sequences of characters for feature e |
| s041 | code | no | pass | None | True | The function determines which event streams receive a broadcast messag |
| s042 | doc | no | flag: Unsupported identifier in answer: `/api/ | None | False | You can retrieve real-time updates about the system's operational stat |
| s043 | doc | no | pass | None | True | The current problem with the ingestion process regarding duplicate fil |
| s044 | code | no | pass | None | True | If the llama command cannot be located on the system's path, the syste |
| s045 | doc | no | flag: Unsupported number in answer: [404] | None | False | User authentication is handled by issuing HS256 bearer tokens from `qp |
| s046 | code | no | pass | None | True | The system identifies expired sessions by checking if the time elapsed |
| s047 | code | no | pass | None | True | The SQL query used to retrieve unique file identifiers from the databa |
| s048 | code | no | pass | None | False | The available testing and maintenance commands include: `uv run pytest |
| s049 | code | no | pass | None | True | The function determines the appropriate level of difficulty instructio |
| s050 | code | no | pass | None | False | The function described in the code snippet is part of the `qp_pipeline |
| s051 | code | no | pass | None | True | The function checks if an email address is already in use by calling ` |
| s052 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The `QP_VERIFY_JUDGE` variable determines the optional judge used for  |
| s053 | code | no | flag: Unsupported identifier in answer: `csv.D | None | True | The method determines the total number of entries in the specified CSV |
| s054 | code | no | pass | None | True | The TextToSpeech object is initialized and made available globally by  |
| s055 | code | no | pass | None | False | The function handles a list containing a single dictionary by falling  |
| s056 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The default command used to launch the server is `llama serve` [1, 2]. |
| s057 | code | no | flag: Unsupported identifier in answer: `RICH_ | None | True | When the rich display option is enabled, the displayed text and format |
| s058 | code | no | pass | None | True | The tags and triplets from the input data are prepared for storage by  |
| s059 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The `profile.html` page handles user account actions, including 'uploa |
| s060 | code | no | pass | None | False | When an external language model service becomes unavailable, the syste |
| s061 | code | no | pass | None | True | The default settings for the VerifyConfig class are: fuzzy_quote_min i |
| s062 | doc | no | pass | None | True | The core components of this local interview practice system include a  |
| s063 | code | no | pass | None | True | A text block is considered a useful table if the number of table rows  |
| s064 | code | no | pass | None | True | The quality score is increased based on several conditions related to  |
| s065 | code | no | pass | None | True | The system retrieves user details when searching by a specific usernam |
| s066 | code | no | pass | None | True | The defined numerical limits for similarity and overlap checks in the  |
| s067 | code | no | pass | None | True | The system tracks repeated failed deletion attempts for a specific ite |
| s068 | code | no | pass | None | True | The function determines which prompt collection to use by first checki |
| s069 | code | no | pass | None | True | The method `DBManager.get_questions_for_file` retrieves questions asso |
| s070 | code | no | flag: no verified quote from cited source(s) [ | None | True | The function responsible for writing chunk information to a CSV file i |
| s071 | code | no | pass | None | False | The final score is modified based on the NLI result type in the follow |
| s072 | doc | no | pass | None | True | The default method for clients to receive event data is by using `Even |
| s073 | code | no | pass | None | True | The system can retrieve a list of files associated with a specific use |
| s074 | code | no | pass | None | True | The system manages and cleans up expired and excessive session tickets |
| s075 | code | no | pass | None | True | The arguments constructed for the llama command include the command fr |
| s076 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The SpeechToText component handles converting audio into text and anal |
| s077 | code | no | pass | None | True | If loading the cross-encoder fails or is stopped, the `_ce_skipped` fl |
| s078 | code | no | flag: the answer cites no source | None | False | The SQL query used to retrieve the similarity hashes and file identifi |
| s079 | doc | no | pass | None | True | The required format for password hashing is a versioned format, such a |
| s080 | code | no | pass | None | False | The function determines if a quote is present in a text chunk through  |
| s081 | doc | no | pass | None | True | D1 is an optional judge, which is off by default [2]. It is a decision |
| s082 | code | no | pass | None | True | When a user deletes a session via `DELETE /api/interview/{sid}`, the s |
| s083 | code | no | flag: Unsupported identifier in answer: `passw | None | True | The system checks the validity of an email and password combination by |
| s084 | code | no | pass | None | True | The report object is considered clean if both `orphan_ids` and `uninde |
| s085 | doc | no | pass | None | True | Phase 1 (auth, device selection, llama lifecycle) and Phase 2 (tests + |
| s086 | code | no | pass | None | True | The analyze_disfluencies function calculates and returns the following |
| s087 | doc | no | pass | None | True | Application settings are managed and loaded through environment variab |
| s088 | code | no | pass | None | True | A text is considered a table of contents if the number of lines matchi |
| s089 | code | no | pass | None | True | The system waits and checks if the LLM service is operational through  |
| s090 | code | no | pass | None | True | When updating a user's email, the system checks if the new email is al |
| s091 | code | no | pass | None | True | When a specific pattern is found in the answer during processing, it r |
| s092 | code | no | flag: Unsupported identifier in answer: `Autho | None | True | The authenticated user's unique identifier is retrieved by calling `ge |
| s093 | code | no | flag: Unsupported number in answer: [260000] | None | True | The system checks if a provided password matches a previously stored h |
| s094 | code | no | pass | None | True | The final output dictionary is constructed by returning a dictionary t |
| s095 | code | no | pass | None | False | The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose |
| s096 | code | no | pass | None | True | The function determines if a word repeats within a defined look-ahead  |
| s097 | code | no | pass | None | True | When combined prompts are not available, the function iterates through |
| s098 | code | no | pass | None | True | Chroma has no reader on the web path [2]. Indexing is kept for planned |
| s099 | code | no | pass | None | True | The session results for a specific user are retrieved using the `DBMan |
| s100 | code | no | pass | None | True | A chunk is processed using an existing summary if `chunk.get("should_u |
| s101 | code | no | flag: the answer cites no source | None | False | The attributes of the TurnResult data structure include question_id (s |
| s102 | code | no | flag: cites sources that do not exist: [9, 11, | None | True | Data discovery can be viewed as two steps: first, the generated data m |
| s103 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The HTTP status codes returned when uploading a file to the ingestion  |
| s104 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The package code is located in `packages/*/src/<package>/`, and the ap |
| s105 | doc | no | pass | None | True | For question generation, you need `llama serve` (llama.cpp) and a GGUF |
| s106 | code | no | pass | None | False | The hardware for running the torch models is determined by checking fo |
| s107 | code | no | flag: Unsupported identifier in answer: `trans | None | False | The audio file is converted into a NumPy array in different ways depen |
| s108 | code | no | flag: Unsupported identifier in answer: `self. | None | True | The class handles returning audio data for the same text input multipl |
| s109 | code | no | pass | None | True | The conditions determining the similarity score and grading method are |
| s110 | doc | no | pass | None | True | The current testing files for the chunk evaluator and ingestion logic  |
| s111 | code | no | pass | None | False | The running language model process is shut down when the QuestionPrep  |
| s112 | code | no | pass | None | False | The system determines which database query to execute based on the spe |
| s113 | code | no | pass | None | True | When a user is deleted, the following database operations are performe |
| s114 | doc | no | pass | None | False | The final verification stage involves checks of provenance and support |
| s115 | code | no | pass | None | True | If the vector indexer fails during user account deletion, the code log |
| s116 | code | no | pass | None | False | The purpose of the function `delete_embeddings_for_file` is to remove  |
| s117 | doc | no | pass | None | False | User authentication is handled by issuing HS256 bearer tokens from `qp |
| s118 | code | no | flag: Unsupported identifier in answer: `new_l | None | True | The function handles lines that start with a specific mask prefix and  |
| s119 | code | no | pass | None | True | The method iterates through `self.block_patterns`, and for each patter |
| s120 | doc | no | pass | None | False | Information about the planned future stages of the project can be foun |
| s121 | code | no | pass | None | True | The LLMUnavailable exception is raised when the LLM server cannot be r |
| s122 | doc | no | pass | None | False | Step 0 and Phase 2 (2.1–2.7) are complete on branch `phase-2`, while P |
| s123 | code | no | pass | None | True | If the initial local operation fails, the fallback mechanism is to log |
| s124 | code | no | flag: Unsupported identifier in answer: `block | None | False | The code snippet in `MarkdownChunker.__init__` defines `block_patterns |
| s125 | doc | no | pass | None | True | The most valuable step taken for scoring calibration was the first pas |
| s126 | code | no | pass | None | False | The lock is used when loading a model to ensure that concurrent first  |
| s127 | code | no | flag: no verified quote from cited source(s) [ | None | True | The function determines the final prediction probabilities for a natur |
| s128 | code | no | flag: Unsupported identifier in answer: `chunk | None | False | The data structure used to prepare the records for insertion into the  |
| s129 | code | no | pass | None | True | The function `chroma_file_ids` maps a chroma id to a file_id, returnin |
| s130 | code | no | pass | None | True | The procedure for terminating the local llama server process if it is  |
| s131 | code | no | pass | None | True | When a user requests their interview history, the system returns a dic |
| s132 | code | no | pass | None | True | The lexical override mechanism is triggered only for true verbatim cop |
| s133 | code | no | pass | None | True | A single-use ticket is validated and removed from storage by popping t |
| s134 | code | no | pass | None | False | The system chooses the number of questions based on the value of `{per |
| s135 | code | no | pass | None | True | The function `count_tokens` determines the number of tokens in a given |
| s136 | doc | no | flag: Unsupported sentence in answer (3 of 5 w | None | True | Following step 0, the dependency order is 0 → 2.1 → {2.2, 2.3, 2.4, 2. |
| s137 | code | no | pass | None | True | The function `_sentence_spans` identifies the starting and ending indi |
| s138 | code | yes | flag: the model returned no parsable answer | None | False | I don't know based on the provided sources. |
| s139 | code | no | flag: Unsupported identifier in answer: `threa | None | True | The `SerializedConverter` class ensures that only one conversion opera |
| s140 | doc | no | flag: no verified quote from cited source(s) [ | None | True | The specific modules that determine the repository root include `_repo |
| s141 | code | no | flag: the answer cites no source | None | False | When the bias score is 0.60 or higher and the final score is less than |
| s142 | code | no | pass | None | True | Data lakes aim to solve the problem where many datasets generated inte |
| s143 | doc | no | pass | None | True | The changes made to the base template and specific files regarding the |
| s144 | code | no | pass | None | True | The goal of this survey is to focus on breadth and identify which data |
| s145 | code | no | flag: no verified quote from cited source(s) [ | None | False | The order of preference for device access is CUDA, then Apple MPS, and |
| s146 | code | no | flag: Unsupported number in answer: [2] | None | True | The method `load_existing_simhashes` in `CSVManager.load_existing_simh |
| s147 | code | no | pass | None | False | A PromptSet builds the (system, user) messages for each LLM stage, whi |
| s148 | code | no | pass | None | True | The system retrieves user details without including the password hash  |
| s149 | doc | no | flag: Unsupported number in answer: [409] | None | True | When a file is uploaded via the ingestion endpoint (`POST /api/files/i |

## Gate policies, same replies re-judged

| policy | answered | flagged | false alarms (correct answers flagged) | errors missed (wrong answers passed) | usable (correct and accepted) | accepted and citing the gold chunk | unanswerable that passed |
|---|---:|---:|---:|---:|---:|---:|---:|
| strict | 148 | 26% (39/148) | 0% (0/0) | 0% (0/0) | 0% (0/149) | 56% (83/149) | 0% (0/0) |
| tolerant | 148 | 26% (38/148) | 0% (0/0) | 0% (0/0) | 0% (0/149) | 56% (84/149) | 0% (0/0) |
| balanced | 148 | 14% (20/148) | 0% (0/0) | 0% (0/0) | 0% (0/149) | 65% (97/149) | 0% (0/0) |
| lenient | 148 | 7% (10/148) | 0% (0/0) | 0% (0/0) | 0% (0/149) | 71% (106/149) | 0% (0/0) |
