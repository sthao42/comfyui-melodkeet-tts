import { app } from "/scripts/app.js";

app.registerExtension({
	name: "Comfy.MelodkeetTTS",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "MelodkeetTTS") {
		}
	},
});
