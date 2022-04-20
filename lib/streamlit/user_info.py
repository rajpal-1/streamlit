from streamlit.scriptrunner import get_script_run_ctx as _get_script_run_ctx
from typing import Mapping, Dict, Optional, Iterator


class UserInfoProxy(Mapping[str, Optional[str]]):
    def __getitem__(self, key):
        ctx = _get_script_run_ctx()
        if ctx is not None:
            user_info = ctx.user_info
            return user_info[key]

    def __getattr__(self, key):
        ctx = _get_script_run_ctx()
        if ctx is not None:
            user_info = ctx.user_info

            try:
                return user_info[key]
            except KeyError:
                raise AttributeError

    def __iter__(self):
        ctx = _get_script_run_ctx()
        if ctx is not None:
            return iter(ctx.user_info)

    def __len__(self) -> int:
        ctx = _get_script_run_ctx()
        if ctx is not None:
            return len(ctx.user_info)
        return 0

    def to_dict(self):
        ctx = _get_script_run_ctx()
        if ctx is not None:
            return ctx.user_info
