"""
Complete Model Metadata for MEDLEY - 34 Models
Including release dates, origins, and bias profiles
Updated August 2025
"""

def get_comprehensive_model_metadata():
    """Return metadata for all 34 models with bias profiles"""
    return {
        # FREE MODELS (10)
        "deepseek/deepseek-r1:free": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2025-01",
            "architecture": "DeepSeek-R1",
            "parameters": "~70B",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["Chinese perspectives", "Mandarin language influence"],
                "demographic_issues": ["Asian-centric viewpoints", "Limited Western cultural nuance"],
                "medical_bias": ["Traditional Chinese Medicine awareness", "Asian disease prevalence patterns"],
                "socioeconomic_bias": "Chinese healthcare system assumptions"
            },
            "strengths": ["Reasoning", "Mathematics", "Code"],
            "cost_tier": "Free"
        },
        
        "deepseek/deepseek-chat:free": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2024-06",
            "architecture": "DeepSeek",
            "parameters": "~67B",
            "training_cutoff": "2024-06",
            "bias_characteristics": {
                "primary_biases": ["Chinese cultural context", "Simplified Chinese optimization"],
                "demographic_issues": ["East Asian perspective dominance"],
                "medical_bias": ["Chinese medical practices", "Asian epidemiology focus"],
                "socioeconomic_bias": "Developing economy perspectives"
            },
            "strengths": ["Multilingual", "General chat"],
            "cost_tier": "Free"
        },
        
        "meta-llama/llama-3.1-70b-instruct:free": {
            "provider": "Meta",
            "origin_country": "USA",
            "release_date": "2024-07",
            "architecture": "Llama-3.1",
            "parameters": "70B",
            "training_cutoff": "2024-07",
            "bias_characteristics": {
                "primary_biases": ["Silicon Valley tech culture", "Facebook/Meta ecosystem"],
                "demographic_issues": ["Social media user demographics"],
                "medical_bias": ["Western medicine focus", "US healthcare system"],
                "socioeconomic_bias": "Developed world assumptions"
            },
            "strengths": ["General reasoning", "Instruction following"],
            "cost_tier": "Free"
        },
        
        "google/gemma-3-27b-it:free": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-11",
            "architecture": "Gemma-3",
            "parameters": "27B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Google's safety filters", "Western tech perspectives"],
                "demographic_issues": ["English-language dominance"],
                "medical_bias": ["Evidence-based medicine focus"],
                "socioeconomic_bias": "Middle-class assumptions"
            },
            "strengths": ["Efficiency", "Safety"],
            "cost_tier": "Free"
        },
        
        "qwen/qwen-2.5-72b-instruct:free": {
            "provider": "Alibaba",
            "origin_country": "China",
            "release_date": "2024-11",
            "architecture": "Qwen-2.5",
            "parameters": "72B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Chinese e-commerce influence", "Alibaba ecosystem"],
                "demographic_issues": ["Chinese internet user base"],
                "medical_bias": ["Chinese healthcare system", "TCM integration"],
                "socioeconomic_bias": "Rapid development economy perspective"
            },
            "strengths": ["Multilingual", "Reasoning", "Code"],
            "cost_tier": "Free"
        },
        
        "nvidia/llama-3.1-nemotron-70b-instruct:free": {
            "provider": "NVIDIA",
            "origin_country": "USA",
            "release_date": "2024-10",
            "architecture": "Nemotron-Llama",
            "parameters": "70B",
            "training_cutoff": "2024-09",
            "bias_characteristics": {
                "primary_biases": ["Technical/engineering focus", "GPU computing bias"],
                "demographic_issues": ["Tech industry perspectives"],
                "medical_bias": ["Medical imaging and AI focus"],
                "socioeconomic_bias": "High-tech industry assumptions"
            },
            "strengths": ["Technical tasks", "Optimization"],
            "cost_tier": "Free"
        },
        
        "mistralai/mistral-7b-instruct:free": {
            "provider": "Mistral AI",
            "origin_country": "France",
            "release_date": "2023-09",
            "architecture": "Mistral",
            "parameters": "7B",
            "training_cutoff": "2023-09",
            "bias_characteristics": {
                "primary_biases": ["European perspectives", "French language influence"],
                "demographic_issues": ["EU-centric viewpoints"],
                "medical_bias": ["European healthcare systems", "Universal healthcare assumptions"],
                "socioeconomic_bias": "European social model"
            },
            "strengths": ["Efficiency", "Speed"],
            "cost_tier": "Free"
        },
        
        "openai/gpt-oss-20b:free": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2024-09",
            "architecture": "GPT-OSS",
            "parameters": "20B",
            "training_cutoff": "2024-08",
            "bias_characteristics": {
                "primary_biases": ["OpenAI safety training", "Silicon Valley culture"],
                "demographic_issues": ["Western perspectives"],
                "medical_bias": ["US medical practices", "FDA-approved treatments focus"],
                "socioeconomic_bias": "Developed economy assumptions"
            },
            "strengths": ["General tasks", "Orchestration"],
            "cost_tier": "Free"
        },
        
        "google/gemma-3-4b-it:free": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-11",
            "architecture": "Gemma-3",
            "parameters": "4B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Simplified responses", "Google safety filters"],
                "demographic_issues": ["Limited nuance due to size"],
                "medical_bias": ["Basic medical knowledge only"],
                "socioeconomic_bias": "Simplified worldview"
            },
            "strengths": ["Speed", "Efficiency"],
            "cost_tier": "Free"
        },
        
        "meta-llama/llama-3.2-3b-instruct:free": {
            "provider": "Meta",
            "origin_country": "USA",
            "release_date": "2024-09",
            "architecture": "Llama-3.2",
            "parameters": "3B",
            "training_cutoff": "2024-09",
            "bias_characteristics": {
                "primary_biases": ["Simplified Meta perspectives", "Mobile-first optimization"],
                "demographic_issues": ["Limited demographic awareness"],
                "medical_bias": ["Basic health information only"],
                "socioeconomic_bias": "Simplified economic understanding"
            },
            "strengths": ["Speed", "Mobile deployment"],
            "cost_tier": "Free"
        },
        
        # PAID MODELS (24)
        "anthropic/claude-sonnet-4": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2025-01",
            "architecture": "Claude-4",
            "parameters": "~500B",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["Constitutional AI principles", "Safety-first approach"],
                "demographic_issues": ["Bay Area tech culture"],
                "medical_bias": ["Evidence-based medicine", "Cautious medical advice"],
                "socioeconomic_bias": "Upper-middle class assumptions"
            },
            "strengths": ["Safety", "Reasoning", "Medical"],
            "cost_tier": "Premium"
        },
        
        "openai/gpt-4o": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2024-05",
            "architecture": "GPT-4-Optimized",
            "parameters": "~200B",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Western cultural bias", "English-language dominance"],
                "demographic_issues": ["Silicon Valley perspectives"],
                "medical_bias": ["Western medicine focus", "US healthcare system"],
                "socioeconomic_bias": "Developed world assumptions"
            },
            "strengths": ["Multimodal", "Reasoning", "Speed"],
            "cost_tier": "Premium"
        },
        
        "anthropic/claude-3.7-sonnet": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-12",
            "architecture": "Claude-3.7",
            "parameters": "~200B",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Anthropic's constitutional AI", "Helpfulness focus"],
                "demographic_issues": ["US-centric training data"],
                "medical_bias": ["Conservative medical recommendations"],
                "socioeconomic_bias": "Educated user assumptions"
            },
            "strengths": ["Balance", "Safety", "Nuance"],
            "cost_tier": "Premium"
        },
        
        "anthropic/claude-3.5-sonnet-20241022": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-10",
            "architecture": "Claude-3.5",
            "parameters": "~175B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Helpful, harmless, honest principles"],
                "demographic_issues": ["Western liberal values"],
                "medical_bias": ["Evidence-based approach", "Risk-averse"],
                "socioeconomic_bias": "Professional class assumptions"
            },
            "strengths": ["Coding", "Analysis", "Writing"],
            "cost_tier": "Premium"
        },
        
        "anthropic/claude-3-opus-20240229": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-02",
            "architecture": "Claude-3",
            "parameters": "~500B",
            "training_cutoff": "2024-02",
            "bias_characteristics": {
                "primary_biases": ["Thorough analysis preference", "Academic style"],
                "demographic_issues": ["Educated audience focus"],
                "medical_bias": ["Comprehensive differential diagnosis"],
                "socioeconomic_bias": "Academic/research orientation"
            },
            "strengths": ["Deep analysis", "Medical", "Research"],
            "cost_tier": "Premium"
        },
        
        "google/gemini-2.5-pro": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12",
            "architecture": "Gemini-2.5",
            "parameters": "~340B",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Google search data influence", "Factual accuracy focus"],
                "demographic_issues": ["Global Google user base"],
                "medical_bias": ["Medical literature emphasis"],
                "socioeconomic_bias": "Information accessibility focus"
            },
            "strengths": ["Factual accuracy", "Multimodal", "Long context"],
            "cost_tier": "Premium"
        },
        
        "deepseek/deepseek-r1": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2025-01",
            "architecture": "DeepSeek-R1",
            "parameters": "~70B",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["Chinese research perspectives", "Mathematical reasoning"],
                "demographic_issues": ["Chinese academic culture"],
                "medical_bias": ["Chinese medical research", "TCM awareness"],
                "socioeconomic_bias": "Chinese economic model"
            },
            "strengths": ["Reasoning", "Mathematics", "Research"],
            "cost_tier": "Standard"
        },
        
        "deepseek/deepseek-chat": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2024-06",
            "architecture": "DeepSeek",
            "parameters": "~67B",
            "training_cutoff": "2024-06",
            "bias_characteristics": {
                "primary_biases": ["Chinese internet culture", "Mandarin optimization"],
                "demographic_issues": ["Chinese user perspectives"],
                "medical_bias": ["Chinese healthcare practices"],
                "socioeconomic_bias": "Emerging market focus"
            },
            "strengths": ["Chat", "Multilingual", "General"],
            "cost_tier": "Standard"
        },
        
        "openai/gpt-4o-mini": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2024-07",
            "architecture": "GPT-4-Optimized",
            "parameters": "~8B",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Simplified GPT-4 perspectives", "Speed optimization"],
                "demographic_issues": ["Reduced nuance"],
                "medical_bias": ["Basic medical knowledge"],
                "socioeconomic_bias": "Simplified worldview"
            },
            "strengths": ["Speed", "Cost-effective", "Basic tasks"],
            "cost_tier": "Budget"
        },
        
        "anthropic/claude-3-haiku-20240307": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-03",
            "architecture": "Claude-3",
            "parameters": "~20B",
            "training_cutoff": "2024-03",
            "bias_characteristics": {
                "primary_biases": ["Concise responses", "Efficiency focus"],
                "demographic_issues": ["Limited context awareness"],
                "medical_bias": ["Basic medical information"],
                "socioeconomic_bias": "Simplified perspectives"
            },
            "strengths": ["Speed", "Efficiency", "Cost"],
            "cost_tier": "Budget"
        },
        
        "google/gemini-2.5-flash": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12",
            "architecture": "Gemini-2.5",
            "parameters": "~80B",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Google ecosystem", "Quick response optimization"],
                "demographic_issues": ["Broad user base"],
                "medical_bias": ["General health information"],
                "socioeconomic_bias": "Mass market assumptions"
            },
            "strengths": ["Speed", "Multimodal", "Efficiency"],
            "cost_tier": "Standard"
        },
        
        "openai/gpt-4-turbo": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2024-04",
            "architecture": "GPT-4-Turbo",
            "parameters": "~170B",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["OpenAI safety training", "JSON optimization"],
                "demographic_issues": ["Developer-focused perspectives"],
                "medical_bias": ["Structured medical responses"],
                "socioeconomic_bias": "Tech industry focus"
            },
            "strengths": ["JSON", "Coding", "Analysis"],
            "cost_tier": "Premium"
        },
        
        "meta-llama/llama-3.1-70b-instruct": {
            "provider": "Meta",
            "origin_country": "USA",
            "release_date": "2024-07",
            "architecture": "Llama-3.1",
            "parameters": "70B",
            "training_cutoff": "2024-07",
            "bias_characteristics": {
                "primary_biases": ["Open-source community values", "Meta ecosystem"],
                "demographic_issues": ["Tech-savvy user base"],
                "medical_bias": ["General medical knowledge"],
                "socioeconomic_bias": "Global internet user perspectives"
            },
            "strengths": ["Reasoning", "Instruction following", "Open"],
            "cost_tier": "Standard"
        },
        
        "google/gemini-2.5-flash-lite": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12",
            "architecture": "Gemini-2.5",
            "parameters": "~20B",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Mobile-first optimization", "Basic responses"],
                "demographic_issues": ["Mobile user focus"],
                "medical_bias": ["Health tips level knowledge"],
                "socioeconomic_bias": "Mass market mobile users"
            },
            "strengths": ["Speed", "Mobile", "Efficiency"],
            "cost_tier": "Budget"
        },
        
        "qwen/qwen-2.5-coder-32b-instruct": {
            "provider": "Alibaba",
            "origin_country": "China",
            "release_date": "2024-11",
            "architecture": "Qwen-2.5",
            "parameters": "32B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Programming focus", "Chinese tech stack"],
                "demographic_issues": ["Developer perspectives"],
                "medical_bias": ["Limited medical knowledge"],
                "socioeconomic_bias": "Tech industry focus"
            },
            "strengths": ["Coding", "Technical tasks"],
            "cost_tier": "Standard"
        },
        
        "mistralai/mistral-large-2411": {
            "provider": "Mistral AI",
            "origin_country": "France",
            "release_date": "2024-11",
            "architecture": "Mistral",
            "parameters": "~123B",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["European values", "French intellectual tradition"],
                "demographic_issues": ["EU perspectives"],
                "medical_bias": ["European medical practices", "GDPR-conscious"],
                "socioeconomic_bias": "European social democracy"
            },
            "strengths": ["Reasoning", "Multilingual", "Analysis"],
            "cost_tier": "Premium"
        },
        
        "anthropic/claude-3.5-haiku-20241022": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-10",
            "architecture": "Claude-3.5",
            "parameters": "~20B",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Brevity preference", "Efficiency"],
                "demographic_issues": ["Limited context"],
                "medical_bias": ["Concise medical summaries"],
                "socioeconomic_bias": "Simplified perspectives"
            },
            "strengths": ["Speed", "Conciseness", "Efficiency"],
            "cost_tier": "Budget"
        },
        
        "x-ai/grok-4": {
            "provider": "xAI",
            "origin_country": "USA",
            "release_date": "2025-01",
            "architecture": "Grok",
            "parameters": "~314B",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["X/Twitter data influence", "Real-time information"],
                "demographic_issues": ["Social media user base"],
                "medical_bias": ["Trending health topics"],
                "socioeconomic_bias": "Tech-libertarian perspectives"
            },
            "strengths": ["Current events", "Humor", "Direct answers"],
            "cost_tier": "Premium"
        },
        
        "cohere/command-r-plus": {
            "provider": "Cohere",
            "origin_country": "Canada",
            "release_date": "2024-03",
            "architecture": "Command-R",
            "parameters": "~104B",
            "training_cutoff": "2024-03",
            "bias_characteristics": {
                "primary_biases": ["Canadian perspectives", "Multilingual focus"],
                "demographic_issues": ["Commonwealth countries"],
                "medical_bias": ["Canadian healthcare system"],
                "socioeconomic_bias": "Universal healthcare assumptions"
            },
            "strengths": ["RAG", "Enterprise", "Multilingual"],
            "cost_tier": "Premium"
        },
        
        "x-ai/grok-2-1212": {
            "provider": "xAI",
            "origin_country": "USA",
            "release_date": "2024-12",
            "architecture": "Grok",
            "parameters": "~170B",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["X platform culture", "Free speech emphasis"],
                "demographic_issues": ["Twitter user demographics"],
                "medical_bias": ["Popular health discussions"],
                "socioeconomic_bias": "Tech entrepreneur perspectives"
            },
            "strengths": ["Real-time", "Direct", "Uncensored"],
            "cost_tier": "Premium"
        },
        
        "openrouter/horizon-beta": {
            "provider": "OpenRouter",
            "origin_country": "USA",
            "release_date": "2024-11",
            "architecture": "Unknown",
            "parameters": "Unknown",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Experimental model", "Unknown training"],
                "demographic_issues": ["Uncertain demographics"],
                "medical_bias": ["Unknown medical training"],
                "socioeconomic_bias": "Uncertain perspectives"
            },
            "strengths": ["Experimental", "Novel approaches"],
            "cost_tier": "Premium"
        },
        
        "perplexity/llama-3.1-sonar-large-128k-online": {
            "provider": "Perplexity",
            "origin_country": "USA",
            "release_date": "2024-08",
            "architecture": "Sonar-Llama",
            "parameters": "70B",
            "training_cutoff": "Real-time",
            "bias_characteristics": {
                "primary_biases": ["Search engine data", "Current information focus"],
                "demographic_issues": ["Internet search users"],
                "medical_bias": ["WebMD-style health information"],
                "socioeconomic_bias": "Information seekers perspective"
            },
            "strengths": ["Online search", "Current info", "Citations"],
            "cost_tier": "Premium"
        },
        
        "ai21/jamba-1.5-large": {
            "provider": "AI21 Labs",
            "origin_country": "Israel",
            "release_date": "2024-08",
            "architecture": "Jamba",
            "parameters": "~398B",
            "training_cutoff": "2024-08",
            "bias_characteristics": {
                "primary_biases": ["Israeli tech perspectives", "Middle Eastern awareness"],
                "demographic_issues": ["Israeli/Middle Eastern context"],
                "medical_bias": ["Israeli healthcare system", "Mediterranean health patterns"],
                "socioeconomic_bias": "Startup nation mentality"
            },
            "strengths": ["Long context", "Structured output", "Reasoning"],
            "cost_tier": "Premium"
        },
        
        "microsoft/wizardlm-2-8x22b": {
            "provider": "Microsoft",
            "origin_country": "USA",
            "release_date": "2024-04",
            "architecture": "WizardLM",
            "parameters": "~141B",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Microsoft ecosystem", "Enterprise focus"],
                "demographic_issues": ["Corporate user base"],
                "medical_bias": ["Healthcare IT perspectives"],
                "socioeconomic_bias": "Enterprise assumptions"
            },
            "strengths": ["Complex reasoning", "Instruction following"],
            "cost_tier": "Premium"
        }
    }

def get_geographical_distribution():
    """Get geographical distribution of models"""
    metadata = get_comprehensive_model_metadata()
    distribution = {}
    
    for model, data in metadata.items():
        country = data.get('origin_country', 'Unknown')
        if country not in distribution:
            distribution[country] = []
        distribution[country].append(model)
    
    return distribution

def get_bias_summary():
    """Get summary of bias patterns across models"""
    metadata = get_comprehensive_model_metadata()
    bias_patterns = {
        "western_bias": [],
        "eastern_bias": [],
        "european_bias": [],
        "tech_bias": [],
        "medical_conservative": [],
        "medical_comprehensive": []
    }
    
    for model, data in metadata.items():
        biases = data.get('bias_characteristics', {})
        primary = biases.get('primary_biases', [])
        
        # Categorize biases
        if any('Western' in b or 'US' in b or 'Silicon Valley' in b for b in primary):
            bias_patterns['western_bias'].append(model)
        if any('Chinese' in b or 'Asian' in b for b in primary):
            bias_patterns['eastern_bias'].append(model)
        if any('European' in b or 'French' in b or 'EU' in b for b in primary):
            bias_patterns['european_bias'].append(model)
        if any('tech' in b.lower() or 'developer' in b.lower() for b in primary):
            bias_patterns['tech_bias'].append(model)
            
        medical = biases.get('medical_bias', '')
        if 'conservative' in medical.lower() or 'cautious' in medical.lower():
            bias_patterns['medical_conservative'].append(model)
        if 'comprehensive' in medical.lower() or 'thorough' in medical.lower():
            bias_patterns['medical_comprehensive'].append(model)
    
    return bias_patterns

if __name__ == "__main__":
    # Print statistics
    metadata = get_comprehensive_model_metadata()
    print(f"Total models with metadata: {len(metadata)}")
    
    geo = get_geographical_distribution()
    print("\nGeographical distribution:")
    for country, models in sorted(geo.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {country}: {len(models)} models")
    
    biases = get_bias_summary()
    print("\nBias patterns:")
    print(f"  Western bias: {len(biases['western_bias'])} models")
    print(f"  Eastern bias: {len(biases['eastern_bias'])} models")
    print(f"  European bias: {len(biases['european_bias'])} models")
    print(f"  Tech industry bias: {len(biases['tech_bias'])} models")