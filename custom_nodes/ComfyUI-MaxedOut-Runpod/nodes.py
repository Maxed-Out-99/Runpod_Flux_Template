import torch
from pathlib import Path
import folder_paths
import comfy.sd


from .install_maxedout import get_model_files, download, MODEL_DIR

class MXD_UNETLoader:
    @classmethod
    def INPUT_TYPES(cls):
        curated = get_model_files()
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
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "load_unet"
    CATEGORY = "MaxedOut/Loaders"

    def load_unet(self, unet_name, weight_dtype):
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

        # Ensure model exists, download if needed
        if not local_path.exists():
            print(f"🔽 Downloading {unet_name} ...")
            download(hf_path, local_path, expected_sha)
        else:
            print(f"✅ {unet_name} found. Skipping download.")

        # Load the UNET model using ComfyUI utils
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
