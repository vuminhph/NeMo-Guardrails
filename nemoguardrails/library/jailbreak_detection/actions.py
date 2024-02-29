# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Optional

from nemoguardrails.actions import action
from nemoguardrails.library.jailbreak_detection.request import (
    jailbreak_detection_heuristics_request,
)
from nemoguardrails.llm.taskmanager import LLMTaskManager

log = logging.getLogger(__name__)


@action()
async def jailbreak_detection_heuristics(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Checks the user's prompt to determine if it is attempt to jailbreak the model."""
    jailbreak_config = llm_task_manager.config.rails.config.jailbreak_detection

    jailbreak_api_url = jailbreak_config.server_endpoint
    lp_threshold = jailbreak_config.length_per_perplexity_threshold
    ps_ppl_threshold = jailbreak_config.prefix_suffix_perplexity_threshold

    prompt = context.get("user_message")

    if not jailbreak_api_url:
        from nemoguardrails.library.jailbreak_detection.heuristics.checks import (
            check_jailbreak_length_per_perplexity,
            check_jailbreak_prefix_suffix_perplexity,
        )

        log.warning(
            "No jailbreak heuristics endpoint set. Running in-process, NOT RECOMMENDED FOR PRODUCTION."
        )
        lp_check = check_jailbreak_length_per_perplexity(prompt, lp_threshold)
        ps_ppl_check = check_jailbreak_prefix_suffix_perplexity(
            prompt, ps_ppl_threshold
        )
        jailbreak = any([lp_check["jailbreak"], ps_ppl_check["jailbreak"]])
        return jailbreak

    jailbreak = await jailbreak_detection_heuristics_request(
        prompt, jailbreak_api_url, lp_threshold, ps_ppl_threshold
    )
    if jailbreak is None:
        log.warning("Jailbreak endpoint not set up properly.")
        # If no result, assume not a jailbreak
        return False
    else:
        return jailbreak
