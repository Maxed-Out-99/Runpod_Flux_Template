import torch
from pathlib import Path
import folder_paths
import comfy.sd

# Assuming these are in your project structure
from .install_maxedout_nodes import get_model_files, download, MODEL_DIR

class MXD_UNETLoader:
    @classmethod
    def INPUT_TYPES(cls):
        curated = get_model_files(schnell=True)
        unet_choices = {}
        
        # Grouped buckets
        fp8 = []
        fp16 = []
        
        for path, local, sha in curated:
            if not local.startswith("diffusion_models/"):
                continue
        
            name = local.split("/")[-1]
            if "-fp8" in name:
                fp8.append((name, path, local, sha))
            elif "-fp16" in name:
                fp16.append((name, path, local, sha))
        
        # Build dict with headers
        cls.UNET_CHOICES = {}
        keys = []
        
        if fp8:
            keys.append("— FP8 —")
            cls.UNET_CHOICES["— FP8 —"] = None
            for name, path, local, sha in sorted(fp8):
                cls.UNET_CHOICES[name] = (path, local, sha)
                keys.append(name)
        
        if fp16:
            keys.append("— FP16 —")
            cls.UNET_CHOICES["— FP16 —"] = None
            for name, path, local, sha in sorted(fp16):
                cls.UNET_CHOICES[name] = (path, local, sha)
                keys.append(name)
        
        return {
            "required": {
                "unet_name": (keys, {"default": fp8[0][0] if fp8 else ""}),
                "weight_dtype": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
                ),
                # --- ADDED TOGGLE ---
                # This adds a boolean toggle to the UI.
                # "default": False makes it OFF by default.
                "auto_download": ("BOOLEAN", {
                    "default": False, 
                    "label_on": "Auto-Download ON", 
                    "label_off": "Auto-Download OFF"
                }),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "load_unet"
    CATEGORY = "MaxedOut/Loaders"

    # --- MODIFIED FUNCTION SIGNATURE ---
    # Added 'auto_download' as a parameter to receive the toggle's state.
    def load_unet(self, unet_name, weight_dtype, auto_download):
        model_options = {}

        if weight_dtype == "fp8_e4m3fn":
            model_options["dtype"] = torch.float8_e4m3fn
        elif weight_dtype == "fp8_e4m3fn_fast":
            model_options["dtype"] = torch.float8_e4m3fn
            model_options["fp8_optimizations"] = True
        elif weight_dtype == "fp8_e5m2":
            model_options["dtype"] = torch.float8_e5m2

        # Resolve full HuggingFace path and expected hash
        meta = self.UNET_CHOICES.get(unet_name)
        if meta is None:
            raise ValueError(f"'{unet_name}' is a section header, not a valid UNET model.")
        
        hf_path, local_rel_path, expected_sha = meta

        local_path = MODEL_DIR / local_rel_path

        # --- MODIFIED DOWNLOAD LOGIC ---
        # Check if model exists
        if not local_path.exists():
            # If model is missing, check the state of the auto_download toggle
            if auto_download:
                print(f"🔽 Auto-download enabled. Downloading {unet_name} ...")
                download(hf_path, local_path, expected_sha)
            else:
                # If auto_download is OFF, raise an error instead of downloading
                raise FileNotFoundError(
                    f"Model '{unet_name}' not found. "
                    "Enable 'Auto-Download' to download it, or select a model you have already downloaded."
                )
        else:
            print(f"✅ {unet_name} found locally. Skipping download.")

        # Load the UNET model using ComfyUI utils
        print("Loading UNET model...")
        model = comfy.sd.load_diffusion_model(str(local_path), model_options=model_options)
        return (model,)

####################################################################################################################################################


# NODE MAPPING
NODE_CLASS_MAPPINGS = {
    "MXD_UNETLoader": MXD_UNETLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MXD_UNETLoader": "(Down)Load UNET MXD",
}
