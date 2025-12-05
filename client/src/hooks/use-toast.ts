import { toast } from "sonner";

type ToastType = "success" | "error" | "info" | "warning";

export const useToast = () => {
  const showToast = (
    message: string,
    type: ToastType = "info",
    options = {}
  ) => {
    switch (type) {
      case "success":
        toast.success(message, options);
        break;
      case "error":
        toast.error(message, options);
        break;
      case "warning":
        toast.warning(message, options);
        break;
      default:
        toast(message, options);
    }
  };

  return { showToast };
};
