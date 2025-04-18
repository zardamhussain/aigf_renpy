

label before_main_menu:
    scene black with fade
    show text "Click anywhere to begin" at truecenter
    pause
    hide text with dissolve
    return


init python:
    
    DONE = False

    def done():
        global DONE
        DONE = True

    renpy.music.register_channel("zardam", "music")

    def ai_voice_callback(event, interact=True, *args, **kwargs):
        """
        event will be 'begin' when dialogue starts,
        and 'end' when it finishes.
        """
        if event == "begin":
            # show talking pose
            renpy.show("ai talking", layer="master")
        elif event == "end":
            # revert to idle pose
            renpy.show("ai idle", layer="master")
        return

    
    def tts_play(query):
        
        url = "https://ai-gf.deno.dev"

        global DONE
        DONE = False

        try:

            if renpy.emscripten:
                
                q = query.replace("\\", "\\\\").replace('"', '\\"')

                js = f"""
                    fetch("https://ai-gf.deno.dev", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ query: "{q}" }})
                    }})
                    .then(response => response.arrayBuffer())                 
                    .then(buffer => {{
                        const blob = new Blob([buffer], {{ type: "audio/mpeg" }});  
                        const url  = URL.createObjectURL(blob);
                        const audio = new Audio(url);
                        audio.onstarted = () => {{
                            console.log("started" ,window)
                            
                        }};
                        audio.play();
                        audio.onplay = () => {{
                            renpy_exec(
                            'renpy.show("ai talking", layer="master"); ' +
                            'renpy.restart_interaction()'
                            );
                        }};

                        audio.onended = () => {{
                            renpy_exec(
                            'renpy.show("ai idle", layer="master"); ' +
                            'renpy.restart_interaction(); ' + 
                            'done()'
                            );
                        }};

                    }})
                    .catch(err => {{
                        console.error("TTS fetch/play error:", err);
                        window._renpy_cmd("notify \\\"TTS error: {q} failed.\\\"");
                    }});
                """



                renpy.emscripten.run_script(js)

                while not DONE:
                    renpy.pause(0.1, hard=True)

                return


            audio_bytes = renpy.fetch(
                url,
                method="POST",
                json={ "query": query },
                result="bytes"
            )

            renpy.show("ai talking", layer="master")
            renpy.with_statement(dissolve)
        
            audio = AudioData(audio_bytes, "tts_output.mp3")
            
            renpy.music.play(audio, channel="zardam", loop=False)

            while renpy.music.is_playing(channel="zardam"):
                renpy.pause(0.1, hard=True)
            
            renpy.show("ai idle", layer="master")
            renpy.with_statement(dissolve)



        except Exception as e:
            print("error", e)
            renpy.notify(f"TTS error: {e}")
            return None



init:

    define config.webaudio_required_types = [ "audio/mpeg" ]


    # Center+scale transform for both poses
    transform ai_center_idle:
        xalign 0.5
        yalign 0.5
        zoom 1.5

    transform ai_center_talk:
        xalign 0.5
        yalign 0.5
        zoom 0.65


    # Declare your two poses, both using the same transform
    image ai idle    =  At("ai_nobg.png", ai_center_idle)
    image ai talking = At("ai_talking_nobg.png", ai_center_talk)


define ai = Character(
    "AI GF",
    image="ai idle",
    callback=ai_voice_callback,
    what_prefix='"', what_suffix='"'
)


label start:

    ai "Hello there! I'm your Alice, nice to meet you"

    $ remaining = 5

    while True:

        $ player_text = renpy.input("Say something...").strip()

        if player_text:
            $ tts_play(player_text)
            $ remaining -= 1
        else:
            "You didn't enter any text."

        if remaining == 0: 
            menu:
                "Do you want to speak again?"
                "Yes":
                    $ remaining = 5
                "No":
                    jump end_demo

    label end_demo:
        "Thanks for trying out the TTS demo!"
        return

