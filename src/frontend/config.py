"""
Request configuration and context.

Translates geneweb/lib/config.ml
Stores all request-specific state and settings.

Integrates with existing models from src/models/
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from enum import Enum
from datetime import datetime, date

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .output import Output, OutputHandler
    from models.date import Date

# Import at runtime for actual use
from .output import Output, OutputHandler


class AuthScheme(Enum):
    """Authentication scheme types"""
    NO_AUTH = "no_auth"
    TOKEN = "token"
    HTTP_BASIC = "http_basic"
    HTTP_DIGEST = "http_digest"


@dataclass
class AuthInfo:
    """Authentication information"""
    scheme: AuthScheme
    user: str = ""
    realm: str = ""


@dataclass
class DateDMY:
    """
    Date in Day-Month-Year format.

    NOTE: This is a simplified version for config.
    For full date handling, use models.date.Date and models.date.DMY
    """
    day: int
    month: int
    year: int
    prec: str = "Sure"  # Sure, About, Maybe, Before, After, etc.


@dataclass
class RequestConfig:
    """
    Main configuration object for a request.

    Translates OCaml Config.config type.
    Contains all request context, environment variables,
    authentication info, and output handler.
    """

    # Basic info
    base_name: str  # Database name
    command: str  # Main command (e.g., "m=P" for person page)
    indep_command: str  # Independent command
    from_addr: str = ""  # Client address

    # Flags
    api_mode: bool = False
    manitou: bool = False  # Super-admin
    supervisor: bool = False
    wizard: bool = False  # Can edit
    friend: bool = False  # Limited access
    just_friend_wizard: bool = False
    semi_public: bool = False
    debug: bool = False
    is_printed_by_template: bool = False
    cgi: bool = True  # CGI mode vs standalone
    predictable_mode: bool = False  # For testing

    # User info
    user: str = ""
    username: str = ""
    userkey: str = ""
    user_iper: Optional[int] = None  # User's person index
    auth: AuthInfo = field(default_factory=lambda: AuthInfo(AuthScheme.NO_AUTH))

    # Environment variables
    env: Dict[str, str] = field(default_factory=dict)  # Query parameters
    senv: Dict[str, str] = field(default_factory=dict)  # Session env
    henv: Dict[str, str] = field(default_factory=dict)  # Hidden env
    base_env: Dict[str, str] = field(default_factory=dict)  # Base config (.gwf file)

    # Language and localization
    lang: str = "en"
    default_lang: str = "en"
    browser_lang: str = "en"
    vowels: List[str] = field(default_factory=list)
    is_rtl: bool = False  # Right-to-left language
    left: str = "left"
    right: str = "right"
    charset: str = "UTF-8"
    lexicon: Dict[str, str] = field(default_factory=dict)  # Translation dictionary

    # Privacy settings
    access_by_key: bool = True
    private_years: int = 150  # Hide living people
    private_years_death: int = 50
    private_years_marriage: int = 50
    hide_names: bool = False
    use_restrict: bool = False
    no_image: bool = False
    no_note: bool = False
    public_if_titles: bool = False
    public_if_no_date: bool = False
    authorized_wizards_notes: bool = False

    # Display settings
    highlight: str = ""
    border: int = 0
    setup_link: bool = False
    multi_parents: bool = False

    # Database info
    nb_of_persons: int = 0
    nb_of_families: int = 0
    default_sosa_ref: Optional[Tuple[int, Optional[any]]] = None  # (iper, person)

    # Paths and URLs
    gw_prefix: str = ""  # Geneweb URL prefix
    images_prefix: str = "images"  # Images URL
    etc_prefix: str = ""  # Static files URL
    auth_file: str = ""  # Authentication file path

    # Request metadata
    request: List[str] = field(default_factory=list)  # Raw request lines
    allowed_titles: List[str] = field(default_factory=list)
    denied_titles: List[str] = field(default_factory=list)
    cgi_passwd: str = ""  # Security token

    # Time and date
    today: DateDMY = field(default_factory=lambda: DateDMY(1, 1, 2025))
    today_wd: int = 0  # Day of week (0=Sunday)
    time: Tuple[int, int, int] = (0, 0, 0)  # (hours, minutes, seconds)
    ctime: float = 0.0  # Current timestamp
    query_start: float = 0.0  # Query start time

    # Connection stats
    n_connect: Optional[Tuple[int, int, int, List[Tuple[str, float]]]] = None
    # (total, wizards, friends, list of (user, time))

    # Output handler
    output: Optional[Output] = None

    # Plugins
    forced_plugins: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)

    # Security
    secret_salt: Optional[str] = None

    def __post_init__(self):
        """Initialize computed fields"""
        if self.output is None:
            # Create default output if none provided
            from .output import StandardOutputHandler
            self.output = Output(StandardOutputHandler())

        # Set today if not set
        if self.today.year == 2025 and self.today.month == 1:
            today_date = date.today()
            self.today = DateDMY(
                day=today_date.day,
                month=today_date.month,
                year=today_date.year
            )
            self.today_wd = today_date.weekday()

        # Set time if not set
        if self.time == (0, 0, 0):
            now = datetime.now()
            self.time = (now.hour, now.minute, now.second)
            self.ctime = now.timestamp()

    def get_env(self, key: str, default: str = "") -> str:
        """Get environment variable from any env dict"""
        return (self.env.get(key) or
                self.henv.get(key) or
                self.senv.get(key) or
                default)

    def get_base_env(self, key: str, default: str = "") -> str:
        """Get base environment variable"""
        return self.base_env.get(key, default)

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.auth.scheme != AuthScheme.NO_AUTH

    @property
    def can_edit(self) -> bool:
        """Check if user can edit database"""
        return self.wizard or self.manitou

    @property
    def prefix(self) -> str:
        """Get URL prefix for links"""
        base = f"?b={self.base_name}" if self.cgi else f"/{self.base_name}"
        return base


def create_empty_config() -> RequestConfig:
    """
    Create an empty/dummy config for testing.
    Translates Config.empty from OCaml.
    """
    return RequestConfig(
        base_name="test",
        command="",
        indep_command=""
    )
