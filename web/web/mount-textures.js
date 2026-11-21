if (typeof document !== "undefined") {
  Module.preRun = [].concat(Module.preRun || []);
  Module.preRun.push(() => {
    const pack = Module.winksTexturePack;
    if (!pack) return;
    addRunDependency("winks-texture-pack");
    pack.blob.arrayBuffer().then(buffer => {
      FS.mkdirTree("/assets/textures");
      FS.createDataFile("/assets/textures", pack.name, new Uint8Array(buffer), true, false, true);
      delete Module.winksTexturePack;
      removeRunDependency("winks-texture-pack");
    }).catch(error => Module.onAbort("Texture pack could not be opened: " + error.message));
  });
}
