from app.settings.setting import Environment, get_settings


class AppConfig:
    """
    Application configuration helper.
    """

    def get_root_path(self) -> str:
        """
        Return the application root path.
        """
        if get_settings().env.environment == Environment.PROD:
            return "/crud/prod"
        return ""


app_config = AppConfig()
