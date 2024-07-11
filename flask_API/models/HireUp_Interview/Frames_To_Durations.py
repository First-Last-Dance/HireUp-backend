def frame_indices_to_durations(frame_indices, fps):
    """
    Converts a list of frame indices to a list of durations.

    Args:
        frame_indices (list): List of frame indices.
        fps (float): Frames per second of the video.

    Returns:
        list: List of durations in the format (start, end).

    Note:
        - The function calculates the time in seconds for each frame index.
        - The start of each duration is rounded down to the nearest lower 0.5 boundary.
        - The end of each duration is calculated as start + 0.5.
        - The durations are returned as a list of tuples.

    """
    durations = []
    for frame_index in frame_indices:
        # Calculate the time in seconds for the current frame index
        time_in_seconds = frame_index / fps
        # Find the nearest lower 0.5 boundary for the start of the interval
        start = (time_in_seconds // 0.5) * 0.5
        end = start + 0.5
        # Append the tuple to the list of durations
        durations.append((start, end))
        
    return durations

def merge_overlapping_durations(durations):
    """
    Merge overlapping durations in a list of intervals.

    Args:
        durations (list): A list of intervals represented as tuples (start, end).

    Returns:
        list: A list of merged intervals.

    Example:
        durations = [(1, 3), (2, 4), (5, 7), (6, 8)]
        merged = merge_overlapping_durations(durations)
        print(merged)  # Output: [(1, 4), (5, 8)]
    """
    if not durations:
        return []

    # Initialize merged durations with the first duration
    merged_durations = [durations[0]]

    for current in durations[1:]:
        # Get the last interval in the merged_durations list
        last = merged_durations[-1]

        # Check if the current interval overlaps with the last interval
        if current[0] <= last[1]:
            # If they overlap, merge the intervals
            merged_durations[-1] = (last[0], max(last[1], current[1]))
        else:
            # If they do not overlap, add the current interval to the list
            merged_durations.append(current)

    return merged_durations
