class_name AudioUtil
extends RefCounted
## Audio helpers usable from @tool scripts (no autoload dependency).


## Returns the stream set to loop (ogg: loop flag; wav: forward loop over all data).
static func looped(stream: AudioStream) -> AudioStream:
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	elif stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = wav.data.size() / (4 if wav.stereo else 2)
	return stream
