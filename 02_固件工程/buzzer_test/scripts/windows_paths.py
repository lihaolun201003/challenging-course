"""Keep the linker map path usable under a Windows Unicode project path."""
import os
Import("env")
if os.name == "nt":
    map_path = os.path.relpath(
        os.path.join(env.subst("$BUILD_DIR"), env.subst("$PROGNAME") + ".map"),
        env.subst("$PROJECT_DIR"),
    ).replace("\\", "/")
    env.Replace(LINKFLAGS=[
        '-Wl,-Map="%s"' % map_path if str(flag).startswith("-Wl,-Map=") else flag
        for flag in env["LINKFLAGS"]
    ])
