# System Resource Tax

Recently I've had an opportunity that's made me more curious about exploring the intersection of ML and system-level performance. In an effort to research the topic, I wanted to put myself in the shoes of a systems engineer and run a small, data-driven investigation into a program I use daily.

I almost always code in VS Code while simultaneously using Spotify. I've been curious if this really impacts my editor's performance. My hypothesis is that a background app (Spotify) creates a "System Resource Tax"—not from its direct CPU usage, but from the constant, hidden overhead of network I/O, which places a "tax" on the whole system.

This project is that investigation. It collects system telemetry under a controlled experiment (with and without music) and then uses a Random Forest model to identify the true drivers of system load.

The main goals of this project were to answer a few key questions that I imagine are central to someone in this field:

1. How do you translate a vague user-facing problem (like "my editor feels slow") into a quantifiable and measurable hypothesis?

2. How can you design a controlled experiment to isolate a single variable's impact from all the other "noise" on a complex system? What simple models can succeed at this task?

3. Finally, how can you use ML models as a tool (not just for prediction) to find the true root cause of a system's behavior?

## Running This Investigation

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Baseline (No Music):**
    First, I needed a "clean" baseline. Close Spotify and other applications completely. Run the logger for 10 minutes while I code normally in VS Code. Once this time has passed, stop logging.

    ```bash
    python src/collect_data.py --app-foreground "Code" --app-background "Spotify" --output data/baseline_log.csv
    ```

3.  **Run Treatment (With Music):**
    Now, we need a "treatment" baseline to compare against. I started streaming music on Spotify (using Lossless audio) and ran the exact same command (with a new output file) for another 10 minutes while coding in a similar fashion.

    ```bash
    python src/collect_data.py --app-foreground "Code" --app-background "Spotify" --output data/treatment_log.csv
    ```

    *(Note: In the future, I'd like to use a longer duration, like 30 minutes, for both steps since it would yield better data.)*

4.  **Analyze:**
    I ran my `src/analyze_data.ipynb` notebook in Jupyter which loads both CSVs, cleans the data, and runs a quick analysis.

    ```bash
    jupyter notebook src/analyze_data.ipynb
    ```

## Results

The investigation confirmed the "System Resource Tax" exists: Spotify streaming increased average system CPU by **52.6%** (from 5.50% to 8.39%). The Random Forest model (R² = 0.88) identified **Spotify's direct CPU usage** as the primary driver (49.62% importance), followed by **network I/O** (27.68% combined). However, I do want to mention an observation I made: CPU spikes up to 32.5% were clearly correlated with skipping songs in the playlist. When skipping, Spotify must decode new audio streams, buffer data, and process metadata which are all CPU-intensive operations. If songs had played continuously without skipping, I imagine my hypothesis would have held and network I/O would likely dominate as the primary driver, as it already accounts for over 27% of importance even with skipping behavior. This investigation should demonstrate that user interactions (like skipping songs) can significantly impact system load, and that the "tax" manifests through both direct CPU consumption and indirect network I/O overhead.

<img width="1389" height="490" alt="image" src="https://github.com/user-attachments/assets/e55a8cb8-93db-4a04-84da-e4e2eef401bb" />
<img width="990" height="590" alt="image" src="https://github.com/user-attachments/assets/fddd823c-f3ab-414b-b90a-03afdba3595b" />
<img width="1389" height="989" alt="image" src="https://github.com/user-attachments/assets/1ad78a25-b311-49b4-a7ac-f0463d368e2d" />
