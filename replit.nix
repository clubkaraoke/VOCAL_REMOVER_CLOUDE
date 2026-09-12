{ pkgs }: {
    deps = [
        pkgs.python310
        pkgs.python310Packages.pip
    ];
    env = {
        PYTHONUNBUFFERED = "1";
    };
}
