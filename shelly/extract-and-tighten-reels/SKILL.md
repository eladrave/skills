---
name: extract-and-tighten-reels
description: Extract topic-focused Instagram Reels from a local spoken video or a folder of videos, then remove filled pauses and tighten pacing while preserving meaning. Use for short interview excerpts, including Hebrew speech, with local processing, per-source output folders, and traceable timestamps.
---

# Extract and tighten Reels

## Outcome

Turn a supplied local spoken video, or each video in a supplied folder, into standalone, topic-focused Reels. Select complete thoughts, remove clearly identified filled pauses, preserve the speaker's meaning and natural speed, and deliver verified MP4 files with source timestamps and an editable cut list.

Support three modes:

- **Select and edit:** analyze a source video, choose excerpts, and produce tightened Reels.
- **Clean existing clips:** tighten the user's selected clips without choosing unrelated content.
- **Analyze only:** recommend excerpts and timestamps without exporting when the user requests analysis or a shortlist only.

Follow the user's current instructions over the defaults below. Do not install this skill or change its configuration as part of processing a video.

## Defaults and intake

Use these defaults when the request does not specify otherwise:

| Setting | Default |
| --- | --- |
| Destination | Instagram Reels |
| Finished duration | 30–50 seconds per clip, after cleanup |
| Framing | 9:16 portrait, usually 1080 × 1920 |
| Speech | Original language, voice, wording, and natural playback speed |
| Selection count | One strong clip per requested topic, with an extra only when it adds distinct value |
| Cleanup | Clear nonlexical fillers and excessive pauses; preserve natural breaths and emphasis |
| Styling | Clean video without added captions, music, logos, or generated footage |
| Processing | Local audio/video processing; no media uploads or paid services |
| Folder input | Process each video directly inside the supplied folder; no recursive scan unless requested |
| Output location | A sibling subfolder named after the source filename with only its final extension removed |

Resolve the source path, requested topics, and any explicit duration or framing requirements from the conversation and available files. If the user names a file in Downloads, check that location directly. Do not make the user provide a file already accessible locally.

If topics are missing, infer useful themes from the request and video when possible. Ask a concise question only when the intended selection would otherwise be materially different. Continue independent inspection while awaiting an answer.

For a coaching interview, the following are useful example topics, not a mandatory classification:

1. Who the process suits.
2. Challenges clients face.
3. Results or benefits of the process.
4. What the coach contributes or works on.

State material assumptions before they affect the edit. Do not request approval for routine cuts already authorized by the task.

## Folder inputs and per-source output folders

Accept a single video, an explicit list of videos, or a folder. For a folder, inventory the supported video files directly inside it and freeze that input list before creating outputs. Inspect files to verify they contain usable video; an extension alone is insufficient. Ignore nonvideo files and generated output folders. Descend into subfolders only when requested, and exclude generated exports from a recursive scan.

Apply the requested topics, duration, cleanup, and verification to each source independently. Do not combine speakers, claims, timestamps, or footage from different files unless the user requests a combined edit. The default selection count applies per source file, not to the folder as a whole.

Create each source's output folder alongside that source, using its exact filename with only the final extension removed. Preserve spaces, Unicode characters, and earlier dots in the name when the filesystem permits them. For example, `Ilanit.interview.v2.mp4` produces `Ilanit.interview.v2/`.

```text
Interviews/
├── A044_07040746_C020.mp4
├── Ilanit_second_interview.mov
├── A044_07040746_C020/
│   ├── 01_who_this_is_for.mp4
│   ├── 02_customer_challenges.mp4
│   ├── 03_process_results.mp4
│   ├── 04_coach_contribution.mp4
│   ├── Selection_Notes.txt
│   ├── Edit_Log.csv
│   ├── Verification.json
│   └── edit_project/
├── Ilanit_second_interview/
│   ├── 01_customer_challenges.mp4
│   ├── 02_client_success_story.mp4
│   ├── Selection_Notes.txt
│   ├── Edit_Log.csv
│   ├── Verification.json
│   └── edit_project/
└── Reel_Batch_Summary.csv
```

The example filenames illustrate possible clips; do not force four clips or invent coverage for a source. Save every extracted video for a source inside its corresponding output folder, together with its notes, verification, and editable project. A user-specified output root overrides the sibling-folder default while preserving the per-source folder names.

Handle existing paths without losing earlier work:

- Reuse an existing source folder only after checking its contents and source ownership. Never empty it or overwrite unrelated files.
- For a revised run, use a numbered run subfolder such as `run_02/` inside the source folder, keeping all of that run's outputs together.
- Reuse completed exports only when the recorded source identity, edit decisions, settings, and verification still match. A matching filename alone is insufficient.
- If different input files have the same stem, retain the required outer stem folder and add distinct per-source subfolders so their exports and metadata cannot overwrite or be mistaken for each other. Record the actual paths in the batch summary.
- If the destination cannot be written, use an authorized writable output location when available and report the actual location. Do not claim the sibling-folder convention was followed if it was not.

Process the full frozen input list. A corrupt file, absent topic, or rendering failure in one source must not stop independent work on other sources. Record per-source status, output paths, clip counts, actual durations, missing topics, failures, and review limitations in `Reel_Batch_Summary.csv`. Preserve existing summaries by versioning them when necessary. Report partial batch completion explicitly.

Keep scratch files separate from exported clips. For analyze-only requests, do not create export folders or render videos unless requested.

## Inspect and preserve the source

1. Verify that each source exists and is readable. Preserve it unchanged.
2. Inspect actual streams with an available local probe such as FFprobe: duration, dimensions, frame rate, time base, rotation, stream start times, audio channels, sample rate, and color metadata.
3. Examine representative frames throughout the relevant footage. Check subject movement, gestures, other speakers, and existing on-screen text before choosing a crop.
4. Inspect audio channels separately. Identify the channel or mix that contains clear dialogue. Do not assume stereo contains two useful channels or always select the left channel.
5. Discover available runtimes and tools. Prefer existing suitable tools. Use an isolated task environment for additional local dependencies when needed. Downloading a model for local inference does not authorize uploading the recording.

Keep intermediates in the workspace's scratch area. Put deliverables in the per-source output folders described above, honoring any explicit output location or host filesystem restriction. Use a new version or run subfolder for revised exports; preserve earlier exports for comparison.

## Transcribe and understand

Generate a local transcript with source-relative segment and word timestamps. Detect the spoken language and use a recognizer appropriate to it. Retain the original-language transcript for editorial decisions; translate summaries only when useful to the user.

Treat transcription as evidence that requires checking:

- General speech recognizers often omit filled pauses or attach them to adjacent words.
- Recognition errors can affect names, numbers, English terms embedded in Hebrew, and word boundaries.
- Prompts that encourage verbatim transcription can also introduce false filler tokens.
- A model's confidence is not proof of the acoustic boundary or of accuracy in an unsupported language.

For Hebrew, prefer a suitable Hebrew-trained recognizer when available. A general multilingual transcript may provide a first pass, but should not be the sole basis for filler removal. Verify model availability and current usage through local package documentation or the model author's documentation when needed.

Inspect the surrounding source whenever a recognition error would change a clip's meaning, a factual claim, or a cut boundary. Do not publish an uncorrected machine transcript as accurate subtitles.

## Select clips for meaning

For each requested topic, find a self-contained passage with:

- An opening that makes sense without the interviewer's question.
- A clear subject and enough context to identify who or what is being discussed.
- A developed point, useful example, or concrete result.
- A complete ending before the next question or unfinished thought.

Prefer clear statements and specific examples over hesitant, abstract passages. Rank candidates by relevance, standalone clarity, specificity, narrative strength, and expected pacing after cleanup.

Keep the distinction between what is actually said and editorial interpretation. A single client's reported outcome remains an example; do not turn it into a typical or guaranteed result. A discussion of coaching focus areas does not establish a complete coaching method.

Prefer continuous excerpts. Join separated passages only when they refer to the same subject, preserve chronology and qualifications, and make a coherent statement. Do not manufacture a causal connection or stronger claim by omitting context. Record and disclose every such join.

If a requested topic is weak or absent, say so. Do not invent coverage or force an unrelated passage into that topic.

Select enough meaningful context to meet the finished duration after filler removal. Keep source handles available for boundary refinement.

## Identify and remove filled pauses

The target is nonlexical hesitation sounds such as “uh,” “um,” “ah,” “ehhh,” “ahmmm,” and equivalent sounds in the source language. Hebrew candidates may be transcribed as אה, אהמ, אממ, or similar spellings.

Do not remove text by substring matching. For example, אהיה is a meaningful Hebrew word, not a filler because it contains אה. Preserve meaningful repetitions, emotional emphasis, qualifiers, and expressions such as “very, very” unless a broader verbal edit is requested.

Use a combination of evidence:

1. Language-appropriate transcription that attempts to retain disfluencies.
2. Playback of each candidate with surrounding speech when audio audition is available.
3. Waveforms, spectrograms, word timing, and pause detection to refine boundaries.
4. A local acoustic filler detector only when its language behavior is suitable and its detections withstand contextual review.

An English-trained detector is not automatically reliable for Hebrew. If a detector produces weak, contradictory, or word-like matches, do not lower its threshold until it generates cuts. Use another source of evidence and record the uncertainty.

For each candidate:

- Identify the preceding and following real words.
- Locate the full filler sound and its decay; do not trust a transcript timestamp alone.
- Preserve word onsets, consonant tails, and sufficient breathing space.
- Cut picture and dialogue together to preserve lip sync.
- Smooth the audio edge with a very short fade when needed to prevent a click. Do not crossfade spoken words over each other.
- Check the resulting join at natural speed when possible.

Shorten excessive silent gaps separately from filled sounds. Silence detection does not detect voiced “um” sounds, and low-volume consonants or breaths are not necessarily silence. Use conservative thresholds and inspect handles around each cut.

False starts, repeated clauses, and discourse words such as “so” are a separate editorial choice. Preserve them during filler-only cleanup unless the user has authorized broader tightening. If they prevent a useful result, propose or clearly identify that additional edit.

Remove all clearly established fillers. If a transition remains ambiguous, preserve the real word and flag the specific ambiguity. Do not claim that every filler is gone unless the review supports that claim.

## Keep the finished clip within scope

Recalculate duration after all cuts. The duration requirement applies to the finished export, not the initial source selection.

If cleanup makes a clip too short, look for adjacent or otherwise coherent source context that adds useful meaning, then clean that material too. Do not retain a known filler, add empty time, repeat footage, stretch speech, or freeze frames just to reach the minimum.

If no truthful, complete excerpt can meet the requested range, report that limitation. A shorter alternative may be delivered with its actual duration and a clear explanation that it falls outside the target.

Keep original speech at 1.0×. Do not use tempo changes, frame-rate reinterpretation, voice synthesis, or lip regeneration to hide cuts or fit the runtime.

## Frame and mix

For portrait conversion, choose the smallest adaptation that preserves the speaker and essential visual content. A consistent crop is appropriate when the subject stays within it. Inspect movement across the entire selected range. Use restrained subject tracking only when required to keep the subject visible.

Scale uniformly. Do not stretch faces, hide essential gestures or text, or add unrequested background replacement, blurred filler, zooms, or decorative transitions. If portrait framing creates a material content tradeoff, prepare an inspectable framing example and explain the issue.

Report when the portrait export enlarges a crop from a landscape source. Output dimensions do not establish native source detail.

Keep dialogue clear and centered. Correct a nearly silent channel or obvious imbalance based on measurements. Apply mild cleanup only when justified. Avoid processing that erases consonants or makes the voice metallic.

Without a supplied audio specification, approximately −16 LUFS integrated with a true-peak ceiling around −1.5 dBTP is a useful starting point. Measure the encoded result. Do not treat these values as universal platform requirements.

Do not add music, captions, titles, or branding unless requested. If captions are requested, generate them from the final edit's timing and correct the wording before delivery.

## Render with an explicit timeline

Maintain an edit decision list with at least:

```json
{
  "clip_id": "03_process_results",
  "topic": "Results of the process",
  "source_file": "/absolute/path/source.mp4",
  "kept_source_ranges_seconds": [[186.4, 191.57], [193.0, 198.0]],
  "removed_ranges": [
    {
      "start": 191.57,
      "end": 193.0,
      "kind": "filled_pause",
      "evidence": "contextual transcription and acoustic boundary review"
    }
  ],
  "playback_speed": 1.0,
  "target_duration_seconds": [30, 50],
  "actual_duration_seconds": null,
  "review_status": "pending"
}
```

The example illustrates the schema only; its ranges are not a complete qualifying clip.

Track source time and finished sequence time separately. Use rational frame rates and consistent frame/sample boundaries. Account for nonzero source starts. Do not assume every source is 30 fps or that each frame corresponds to an integer number of audio samples.

Render from the original source rather than repeatedly encoding earlier delivery files. Preserve the intended frame cadence. A usual delivery is H.264 video, AAC audio, a compatible pixel format, and fast-start MP4.

Measure sample counts and timestamps after audio processing. Filters or encoders can add padding or produce discontinuous timestamps. If that happens, fix the processing clock or remove demonstrated processing-only padding. Derive the correct length from the retained source samples, never from an arbitrary target runtime. Do not use a forced export duration or “shortest stream” option to conceal a mismatch.

Save the actual ranges, render configuration, and a working local render command. Use bounded parallel rendering only when outputs and intermediates have separate ownership and the machine has sufficient resources.

## Verify before delivery

Verify the final encoded files, not just intermediate audio or a successful render command.

**Editorial and listening review**

- Review each short clip completely at natural speed when the environment supports audiovisual playback.
- Check every cut and every join between separated passages.
- Confirm the opening is understandable, the ending is complete, and omissions preserve meaning.
- Check for remaining fillers, clipped words, unnatural cadence, clicks, and distracting jumps.
- Use a second transcription pass to find missing words or remaining filler candidates. Treat it as a diagnostic, not a replacement for listening.

**Technical review**

- Probe actual duration, dimensions, codecs, frame rate, channel layout, and audio/video stream lengths.
- Decode all streams completely and investigate errors.
- Inspect encoded frames at the start and end of retained sections for framing and visual continuity.
- Check that audio and video cuts follow the same source mapping and stay synchronized.
- Recheck encoded loudness and true peak.
- Investigate unexpected timing differences; distinguish codec rounding from genuine drift or missing content.

If complete playback or listening is unavailable, state exactly which checks were completed and which remain unverified. Deliver useful outputs with explicit review limits. Do not label an automated pass as exhaustive human-equivalent listening or promise that all fillers were removed.

Once relevant checks pass, do not repeat them without a new edit, failure, or unresolved concern.

## Deliverables and final response

For an editing request, provide:

1. One usable MP4 per selected clip, with descriptive numbered filenames.
2. A concise selection note explaining each topic, source timestamps, and why the clip works.
3. An edit log distinguishing filled-pause cuts, shortened silence, and joins between separate passages.
4. The final timeline and a reproducible local render script or project.
5. A verification record with actual durations and review limits.
6. A ZIP containing the requested clips and supporting files when convenient.

For folder input, keep these deliverables in each source's own folder and provide the batch summary at the input-folder or chosen output-root level. A batch ZIP, when provided, must retain the per-source folder structure. Summarize every input's outcome, including files that produced no usable clips or could not be processed.

When revising existing clips, keep the originals and report before/after durations. Recommend the strongest clip when the evidence supports a useful ranking.

Use verified, absolute output-file links in the response. Keep the final response concise: state what was produced, list the clips and durations, link the bundle and notes, and disclose material limitations. State whether media stayed local and whether anything was published. Do not upload or publish as an implied finishing step.
