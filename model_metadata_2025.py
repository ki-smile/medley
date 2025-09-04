"""
Comprehensive Model Metadata Database for 2025
Includes bias analysis, origins, release dates, and characteristics
"""

from datetime import datetime
from typing import Dict, List, Any

def get_comprehensive_model_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Comprehensive metadata for all models in the Medley system
    Updated for 2025 with bias analysis and recent model information
    """
    
    metadata = {
        # OpenAI Models
        "openai/gpt-4o": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2024-05-13",
            "parameters": "~200B",
            "architecture": "Transformer",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Western cultural bias", "English-language dominance", "Silicon Valley perspectives"],
                "demographic_issues": ["Underrepresentation of Global South perspectives", "Tech industry overrepresentation"],
                "medical_bias": ["Western medicine focus", "Limited traditional/alternative medicine knowledge"],
                "socioeconomic_bias": "Tends toward middle/upper-class assumptions"
            },
            "strengths": ["Safety training", "Multimodal capabilities", "Reasoning"],
            "limitations": ["Proprietary", "API-dependent", "Western bias"],
            "cost_tier": "Premium"
        },
        
        "openai/gpt-4o-mini": {
            "provider": "OpenAI", 
            "origin_country": "USA",
            "release_date": "2024-07-18",
            "parameters": "~8B",
            "architecture": "Transformer",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Similar to GPT-4o but potentially less refined"],
                "demographic_issues": ["Western-centric viewpoints"],
                "medical_bias": ["Standard Western medical paradigm"],
                "socioeconomic_bias": "Cost-optimized may mean less diverse training"
            },
            "strengths": ["Cost-effective", "Fast inference", "Good performance"],
            "limitations": ["Smaller capacity", "Less nuanced than full GPT-4o"],
            "cost_tier": "Budget"
        },
        
        "openai/gpt-oss-120b": {
            "provider": "OpenAI",
            "origin_country": "USA",
            "release_date": "2025-08-05",
            "parameters": "117B total, 5.1B active (MoE)",
            "architecture": "Mixture-of-Experts Transformer", 
            "training_cutoff": "2025-06",
            "bias_characteristics": {
                "primary_biases": ["Open-weight but trained on Western data"],
                "demographic_issues": ["Similar training biases to proprietary models"],
                "medical_bias": ["2025 medical knowledge, Western-centric"],
                "socioeconomic_bias": "Consumer hardware optimization may democratize access"
            },
            "strengths": ["Open-weight", "Apache 2.0 license", "Efficient inference", "Strong reasoning"],
            "limitations": ["Still Western-trained", "MoE complexity", "Large memory requirements"],
            "cost_tier": "Open Source"
        },
        
        # Anthropic Models
        "anthropic/claude-3-opus-20240229": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-02-29",
            "parameters": "~175B",
            "architecture": "Constitutional AI Transformer",
            "training_cutoff": "2023-08",
            "bias_characteristics": {
                "primary_biases": ["Constitutional AI safety bias", "Academic/philosophical orientation"],
                "demographic_issues": ["Western liberal values emphasis"],
                "medical_bias": ["Evidence-based medicine focus", "Ethical medical frameworks"],
                "socioeconomic_bias": "Academic/intellectual class perspectives"
            },
            "strengths": ["Safety focus", "Ethical reasoning", "Long context"],
            "limitations": ["Conservative responses", "Western ethics focus"],
            "cost_tier": "Premium"
        },
        
        "anthropic/claude-3-sonnet-20240229": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-02-29", 
            "parameters": "~70B",
            "architecture": "Constitutional AI Transformer",
            "training_cutoff": "2023-08",
            "bias_characteristics": {
                "primary_biases": ["Balanced safety vs capability", "Western ethical framework"],
                "demographic_issues": ["Moderate Western bias"],
                "medical_bias": ["Balanced medical approach", "Safety-first medical advice"],
                "socioeconomic_bias": "Middle-ground socioeconomic perspectives"
            },
            "strengths": ["Balanced performance", "Good safety", "Reasonable cost"],
            "limitations": ["Mid-tier capabilities", "Western-centric"],
            "cost_tier": "Mid-Range"
        },
        
        "anthropic/claude-3-haiku-20240307": {
            "provider": "Anthropic",
            "origin_country": "USA",
            "release_date": "2024-03-07",
            "parameters": "~20B",
            "architecture": "Constitutional AI Transformer",
            "training_cutoff": "2023-08", 
            "bias_characteristics": {
                "primary_biases": ["Fast response optimization", "Safety over nuance"],
                "demographic_issues": ["Simplified Western perspectives"],
                "medical_bias": ["Conservative medical advice", "Safety-first approach"],
                "socioeconomic_bias": "Cost-optimized may reduce diversity"
            },
            "strengths": ["Fast", "Cost-effective", "Safe"],
            "limitations": ["Less capable", "Simplified responses"],
            "cost_tier": "Budget"
        },
        
        # Google Models
        "google/gemini-2.5-pro": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12-19",
            "parameters": "Unknown",
            "architecture": "Multimodal Transformer",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Tech industry perspectives", "Google ecosystem integration"],
                "demographic_issues": ["Silicon Valley culture", "Tech-savvy user assumptions"],
                "medical_bias": ["Evidence-based with Google Health influence", "Digital health focus"],
                "socioeconomic_bias": "Tech industry income levels and perspectives"
            },
            "strengths": ["Latest knowledge", "Multimodal", "Integration capabilities"],
            "limitations": ["Google ecosystem dependency", "Tech industry bias"],
            "cost_tier": "Premium"
        },
        
        "google/gemini-2.5-flash": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12-19",
            "parameters": "Unknown",
            "architecture": "Optimized Multimodal Transformer with Thinking",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Speed-focused optimization", "Google ecosystem bias"],
                "demographic_issues": ["Tech-savvy user base assumptions"],
                "medical_bias": ["Latest medical knowledge but Western-focused"],
                "socioeconomic_bias": "Optimized for commercial use cases"
            },
            "strengths": ["Ultra-fast inference", "Advanced reasoning", "Thinking capabilities", "Cost-effective"],
            "limitations": ["May prioritize speed over depth", "Google-specific optimizations"],
            "cost_tier": "Budget-Premium"
        },
        
        "google/gemini-2.5-flash-lite": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12-19",
            "parameters": "Unknown (lightweight)",
            "architecture": "Lightweight Multimodal Transformer",
            "training_cutoff": "2024-11",
            "bias_characteristics": {
                "primary_biases": ["Ultra-speed optimization", "Simplified reasoning"],
                "demographic_issues": ["Mobile/edge device user assumptions"],
                "medical_bias": ["Basic medical knowledge, may miss nuances"],
                "socioeconomic_bias": "Optimized for resource-constrained environments"
            },
            "strengths": ["Extremely fast", "Low latency", "Cost-efficient", "Edge deployment"],
            "limitations": ["Reduced capability vs full Flash", "May oversimplify complex cases"],
            "cost_tier": "Budget"
        },
        
        "google/gemini-2.0-flash-exp": {
            "provider": "Google",
            "origin_country": "USA",
            "release_date": "2024-12-11",
            "parameters": "Unknown",
            "architecture": "Optimized Multimodal Transformer",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Speed optimization", "Experimental features"],
                "demographic_issues": ["Tech-forward perspectives"],
                "medical_bias": ["Modern medical focus", "Technology-enhanced healthcare"],
                "socioeconomic_bias": "Early adopter demographics"
            },
            "strengths": ["Fast inference", "Experimental features", "Multimodal"],
            "limitations": ["Experimental stability", "Google-specific optimizations"],
            "cost_tier": "Mid-Range"
        },
        
        "google/gemma-2-9b-it": {
            "provider": "Google",
            "origin_country": "USA", 
            "release_date": "2024-06-27",
            "parameters": "9B",
            "architecture": "Open Transformer",
            "training_cutoff": "2024-04",
            "bias_characteristics": {
                "primary_biases": ["Open model with Google values", "Instruction-tuned responses"],
                "demographic_issues": ["Western tech culture"],
                "medical_bias": ["Google Health data influence", "Consumer health focus"],
                "socioeconomic_bias": "Consumer-focused healthcare perspectives"
            },
            "strengths": ["Open weights", "Efficient", "Good instruction following"],
            "limitations": ["Smaller model", "Google-centric training"],
            "cost_tier": "Free"
        },
        
        # Meta Models
        "meta-llama/llama-3.2-3b-instruct": {
            "provider": "Meta",
            "origin_country": "USA",
            "release_date": "2024-09-25",
            "parameters": "3B",
            "architecture": "Llama Transformer",
            "training_cutoff": "2024-07",
            "bias_characteristics": {
                "primary_biases": ["Social media data influence", "Global connectivity focus"],
                "demographic_issues": ["Facebook/Instagram user demographics", "Social media biases"],
                "medical_bias": ["Social health discussions", "Viral health information patterns"],
                "socioeconomic_bias": "Social media user base diversity but platform biases"
            },
            "strengths": ["Open source", "Social awareness", "Diverse training data"],
            "limitations": ["Small model", "Social media biases", "Misinformation exposure"],
            "cost_tier": "Free"
        },
        
        # Mistral Models
        "mistralai/mistral-large-2411": {
            "provider": "Mistral AI",
            "origin_country": "France",
            "release_date": "2024-11-01",
            "parameters": "~123B",
            "architecture": "Mixture-of-Experts",
            "training_cutoff": "2024-09",
            "bias_characteristics": {
                "primary_biases": ["European perspectives", "GDPR-compliant training", "French cultural influence"],
                "demographic_issues": ["European-centric views", "EU regulatory compliance"],
                "medical_bias": ["European healthcare systems", "Universal healthcare assumptions"],
                "socioeconomic_bias": "European social democratic values"
            },
            "strengths": ["European perspective", "Privacy-focused", "Strong reasoning"],
            "limitations": ["European bias", "Limited global South representation"],
            "cost_tier": "Premium"
        },
        
        "mistralai/mistral-small-2402": {
            "provider": "Mistral AI", 
            "origin_country": "France",
            "release_date": "2024-02-01",
            "parameters": "~22B",
            "architecture": "Transformer",
            "training_cutoff": "2024-01",
            "bias_characteristics": {
                "primary_biases": ["European startup culture", "French language influence"],
                "demographic_issues": ["European user base", "Western education systems"],
                "medical_bias": ["European medical standards", "Socialized healthcare context"],
                "socioeconomic_bias": "European middle-class perspectives"
            },
            "strengths": ["European alternative", "Cost-effective", "Privacy-aware"],
            "limitations": ["Smaller capacity", "European-centric"],
            "cost_tier": "Budget"
        },
        
        "mistralai/mistral-7b-instruct": {
            "provider": "Mistral AI",
            "origin_country": "France", 
            "release_date": "2023-09-27",
            "parameters": "7B",
            "architecture": "Transformer",
            "training_cutoff": "2023-07",
            "bias_characteristics": {
                "primary_biases": ["Early open European model", "French AI research influence"],
                "demographic_issues": ["Academic European perspectives"],
                "medical_bias": ["Traditional European medicine", "Academic medical training"],
                "socioeconomic_bias": "Academic and startup ecosystem perspectives"
            },
            "strengths": ["Open source", "European origin", "Research-friendly"],
            "limitations": ["Older training", "Limited parameters", "European focus"],
            "cost_tier": "Free"
        },
        
        # Chinese Models
        "deepseek/deepseek-chat": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2024-12-20",
            "parameters": "671B total, 37B active (MoE)",
            "architecture": "Mixture-of-Experts",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Chinese cultural perspectives", "Confucian values", "Collective social harmony"],
                "demographic_issues": ["Han Chinese majority perspective", "Chinese internet culture"],
                "medical_bias": ["Traditional Chinese Medicine integration", "Chinese healthcare system"],
                "socioeconomic_bias": "Chinese middle-class urban perspectives"
            },
            "strengths": ["Chinese cultural knowledge", "Cost-effective", "Advanced reasoning"],
            "limitations": ["Chinese censorship influence", "Limited Western perspectives"],
            "cost_tier": "Budget"
        },
        
        "deepseek/deepseek-r1": {
            "provider": "DeepSeek",
            "origin_country": "China",
            "release_date": "2025-01-20",
            "parameters": "671B total, 37B active (MoE)",
            "architecture": "Reasoning-optimized MoE",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["Chinese reasoning patterns", "Analytical thinking focus"],
                "demographic_issues": ["Chinese educational system influence"],
                "medical_bias": ["Evidence-based with Chinese medical practice"],
                "socioeconomic_bias": "Chinese economic development perspective"
            },
            "strengths": ["Advanced reasoning", "Chinese perspectives", "Open source"],
            "limitations": ["Reasoning focus may miss emotional aspects", "Chinese regulatory constraints"],
            "cost_tier": "Free"
        },
        
        "01-ai/yi-large": {
            "provider": "01.AI",
            "origin_country": "China",
            "release_date": "2024-05-13",
            "parameters": "~100B",
            "architecture": "Transformer",
            "training_cutoff": "2024-03",
            "bias_characteristics": {
                "primary_biases": ["Chinese tech industry", "Kai-Fu Lee's AI philosophy"],
                "demographic_issues": ["Chinese urban professional class"],
                "medical_bias": ["Chinese healthcare innovation", "Digital health focus"],
                "socioeconomic_bias": "Chinese tech entrepreneur perspectives"
            },
            "strengths": ["Chinese AI expertise", "Business-oriented", "Practical applications"],
            "limitations": ["Chinese market focus", "Limited global diversity"],
            "cost_tier": "Mid-Range"
        },
        
        "qwen/qwen-2.5-coder-32b-instruct": {
            "provider": "Alibaba",
            "origin_country": "China",
            "release_date": "2024-11-12",
            "parameters": "32B",
            "architecture": "Code-specialized Transformer",
            "training_cutoff": "2024-09",
            "bias_characteristics": {
                "primary_biases": ["Chinese tech industry", "Alibaba ecosystem", "E-commerce focus"],
                "demographic_issues": ["Chinese developer community", "Asian programming practices"],
                "medical_bias": ["Healthcare technology", "Chinese medical informatics"],
                "socioeconomic_bias": "Chinese tech industry and e-commerce perspectives"
            },
            "strengths": ["Chinese tech knowledge", "Code specialization", "E-commerce expertise"],
            "limitations": ["Code-focused", "Chinese platform bias", "Limited medical focus"],
            "cost_tier": "Mid-Range"
        },
        
        # Other International Models
        "cohere/command-r-plus": {
            "provider": "Cohere",
            "origin_country": "Canada",
            "release_date": "2024-04-04",
            "parameters": "~104B",
            "architecture": "Transformer",
            "training_cutoff": "2024-02",
            "bias_characteristics": {
                "primary_biases": ["Canadian multicultural values", "Enterprise focus", "Commonwealth perspectives"],
                "demographic_issues": ["Canadian diversity", "Professional/enterprise user base"],
                "medical_bias": ["Canadian healthcare system", "Multicultural health approaches"],
                "socioeconomic_bias": "Canadian middle-class and professional perspectives"
            },
            "strengths": ["Multicultural training", "Enterprise features", "Canadian values"],
            "limitations": ["Enterprise focus", "Canadian-centric", "Limited availability"],
            "cost_tier": "Premium"
        },
        
        "cohere/command-r": {
            "provider": "Cohere", 
            "origin_country": "Canada",
            "release_date": "2024-03-11",
            "parameters": "~35B",
            "architecture": "Transformer",
            "training_cutoff": "2024-01",
            "bias_characteristics": {
                "primary_biases": ["Canadian perspectives", "RAG-optimized responses"],
                "demographic_issues": ["Canadian multicultural approach"],
                "medical_bias": ["Canadian healthcare focus", "Evidence-based medicine"],
                "socioeconomic_bias": "Canadian social safety net assumptions"
            },
            "strengths": ["RAG capabilities", "Canadian diversity", "Enterprise focus"],
            "limitations": ["Smaller than Plus version", "Canadian-centric"],
            "cost_tier": "Mid-Range"
        },
        
        # Specialized Models
        "shisa-ai/shisa-v2-llama3.3-70b": {
            "provider": "Shisa.AI",
            "origin_country": "Japan/USA",
            "release_date": "2024-12-20",
            "parameters": "70B",
            "architecture": "Bilingual Fine-tuned Llama",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Japanese-English bilingual", "East Asian cultural perspectives", "Academic research focus"],
                "demographic_issues": ["Japanese cultural values", "East Asian demographics"],
                "medical_bias": ["Japanese healthcare system", "East Asian medical practices"],
                "socioeconomic_bias": "Japanese social harmony and consensus-building"
            },
            "strengths": ["Bilingual capability", "Japanese cultural knowledge", "Academic rigor"],
            "limitations": ["Japanese-English focus", "Limited other language support"],
            "cost_tier": "Free"
        },
        
        "ai21/jamba-large-1.7": {
            "provider": "AI21 Labs",
            "origin_country": "Israel",
            "release_date": "2025-07-01",
            "parameters": "94B active/398B total (MoE)",
            "architecture": "Hybrid SSM-Transformer (Jamba)",
            "training_cutoff": "2024-08-22",
            "bias_characteristics": {
                "primary_biases": ["Israeli tech innovation", "Middle Eastern perspectives", "Hebrew language influence"],
                "demographic_issues": ["Israeli startup culture", "Middle Eastern viewpoints"],
                "medical_bias": ["Israeli medical innovation", "Middle Eastern health challenges"],
                "socioeconomic_bias": "Israeli high-tech industry perspectives"
            },
            "strengths": ["Long context (256K)", "Israeli innovation", "Hybrid architecture"],
            "limitations": ["Israeli-centric", "Complex architecture", "Western bias acknowledged"],
            "cost_tier": "Premium"
        },
        
        "perplexity/sonar-deep-research": {
            "provider": "Perplexity AI",
            "origin_country": "USA",
            "release_date": "2025-03-07",
            "parameters": "70B (based on Llama 3.3)",
            "architecture": "Search-augmented Transformer",
            "training_cutoff": "2025-02",
            "bias_characteristics": {
                "primary_biases": ["Search result bias", "Web content bias", "Real-time information focus"],
                "demographic_issues": ["Internet user demographics", "English web dominance"],
                "medical_bias": ["Web health information bias", "Search ranking influences"],
                "socioeconomic_bias": "Internet-connected population perspectives"
            },
            "strengths": ["Real-time information", "Source citation", "Research focus"],
            "limitations": ["Web bias", "Search bubble effects", "Information quality varies"],
            "cost_tier": "Premium"
        },
        
        # Microsoft/Other Models
        "microsoft/wizardlm-2-8x22b": {
            "provider": "Microsoft",
            "origin_country": "USA",
            "release_date": "2024-04-15",
            "parameters": "8x22B (MoE)",
            "architecture": "Mixture-of-Experts",
            "training_cutoff": "2024-02",
            "bias_characteristics": {
                "primary_biases": ["Microsoft enterprise focus", "Windows ecosystem", "Business applications"],
                "demographic_issues": ["Enterprise user demographics", "Western business culture"],
                "medical_bias": ["Healthcare IT focus", "Microsoft Health initiatives"],
                "socioeconomic_bias": "Corporate enterprise perspectives"
            },
            "strengths": ["Enterprise features", "Microsoft integration", "Complex reasoning"],
            "limitations": ["Enterprise bias", "Microsoft ecosystem dependency"],
            "cost_tier": "Premium"
        },
        
        "x-ai/grok-2-1212": {
            "provider": "xAI",
            "origin_country": "USA",
            "release_date": "2024-12-12",
            "parameters": "Unknown",
            "architecture": "Transformer",
            "training_cutoff": "2024-10",
            "bias_characteristics": {
                "primary_biases": ["Elon Musk's perspectives", "Twitter/X data influence", "Contrarian viewpoints"],
                "demographic_issues": ["Twitter user demographics", "Tech libertarian views"],
                "medical_bias": ["Skeptical of medical establishment", "Alternative viewpoints"],
                "socioeconomic_bias": "Tech entrepreneur and Twitter user perspectives"
            },
            "strengths": ["Contrarian perspectives", "Real-time X integration", "Uncensored responses"],
            "limitations": ["Strong ideological bias", "Controversial viewpoints", "Polarizing"],
            "cost_tier": "Premium"
        },
        
        "x-ai/grok-4": {
            "provider": "xAI", 
            "origin_country": "USA",
            "release_date": "2024-12-26",
            "parameters": "Unknown (advanced)",
            "architecture": "Advanced Transformer",
            "training_cutoff": "2024-12",
            "bias_characteristics": {
                "primary_biases": ["Enhanced contrarian views", "X platform integration", "Free speech absolutism"],
                "demographic_issues": ["X user demographics", "Tech industry perspectives"],
                "medical_bias": ["Medical skepticism", "Alternative health promotion"],
                "socioeconomic_bias": "Tech libertarian and entrepreneur perspectives"
            },
            "strengths": ["Latest version", "Uncensored", "Real-time capabilities"],
            "limitations": ["Strong bias", "Controversial", "Potentially harmful medical advice"],
            "cost_tier": "Ultra-Premium"
        },
        
        # Smaller/Specialized Models
        "liquid/lfm-40b": {
            "provider": "Liquid AI",
            "origin_country": "USA",
            "release_date": "2024-10-29",
            "parameters": "40B",
            "architecture": "Liquid Foundation Model",
            "training_cutoff": "2024-08",
            "bias_characteristics": {
                "primary_biases": ["Novel architecture bias", "Research-focused", "MIT influence"],
                "demographic_issues": ["Academic research community"],
                "medical_bias": ["Research-oriented medical knowledge"],
                "socioeconomic_bias": "Academic and research institution perspectives"
            },
            "strengths": ["Novel architecture", "Research innovation", "Academic backing"],
            "limitations": ["Experimental", "Limited deployment", "Research focus"],
            "cost_tier": "Free"
        },
        
        "nousresearch/hermes-3-llama-3.1-8b": {
            "provider": "NousResearch",
            "origin_country": "USA",
            "release_date": "2024-08-27",
            "parameters": "8B",
            "architecture": "Fine-tuned Llama",
            "training_cutoff": "2024-06",
            "bias_characteristics": {
                "primary_biases": ["Open source community", "Uncensored training", "Research freedom"],
                "demographic_issues": ["Open source developer community"],
                "medical_bias": ["Uncensored medical information", "Research-oriented"],
                "socioeconomic_bias": "Open source community values"
            },
            "strengths": ["Uncensored", "Open source", "Community-driven"],
            "limitations": ["Smaller model", "Limited safety training", "Potential harmful outputs"],
            "cost_tier": "Free"
        },
        
        "perplexity/llama-3.1-sonar-small-128k-online": {
            "provider": "Perplexity AI",
            "origin_country": "USA", 
            "release_date": "2024-07-23",
            "parameters": "8B",
            "architecture": "Search-augmented Llama",
            "training_cutoff": "2024-06",
            "bias_characteristics": {
                "primary_biases": ["Search-based information", "Online content bias"],
                "demographic_issues": ["Internet user demographics"],
                "medical_bias": ["Web health information", "Search ranking bias"],
                "socioeconomic_bias": "Online population perspectives"
            },
            "strengths": ["Real-time search", "Citations", "Up-to-date info"],
            "limitations": ["Search bias", "Web quality issues", "Smaller model"],
            "cost_tier": "Budget"
        }
    }
    
    return metadata

def get_model_bias_summary(model_id: str) -> Dict[str, str]:
    """Get a concise bias summary for a specific model"""
    metadata = get_comprehensive_model_metadata()
    
    if model_id not in metadata:
        return {
            "origin_bias": "Unknown origin",
            "cultural_bias": "Unknown cultural influence",
            "medical_bias": "Unknown medical perspective",
            "risk_level": "Unknown"
        }
    
    model_info = metadata[model_id]
    bias_info = model_info.get("bias_characteristics", {})
    
    # Determine risk level based on bias characteristics
    risk_indicators = []
    if "Contrarian" in str(bias_info.get("primary_biases", [])):
        risk_indicators.append("High")
    if "Uncensored" in str(bias_info.get("primary_biases", [])):
        risk_indicators.append("High") 
    if model_info.get("origin_country") in ["China"]:
        risk_indicators.append("Medium")
    if "medical skepticism" in str(bias_info.get("medical_bias", "")).lower():
        risk_indicators.append("High")
    
    risk_level = "High" if "High" in risk_indicators else "Medium" if risk_indicators else "Low"
    
    return {
        "origin_bias": f"{model_info.get('origin_country', 'Unknown')} cultural perspective",
        "cultural_bias": bias_info.get("primary_biases", ["Unknown"])[0] if bias_info.get("primary_biases") else "Unknown",
        "medical_bias": bias_info.get("medical_bias", "Unknown medical perspective"),
        "risk_level": risk_level
    }

def get_geographical_distribution() -> Dict[str, List[str]]:
    """Get geographical distribution of models by origin country"""
    metadata = get_comprehensive_model_metadata()
    
    distribution = {}
    for model_id, info in metadata.items():
        country = info.get("origin_country", "Unknown")
        if country not in distribution:
            distribution[country] = []
        distribution[country].append(model_id)
    
    return distribution

if __name__ == "__main__":
    # Print summary statistics
    metadata = get_comprehensive_model_metadata()
    geo_dist = get_geographical_distribution()
    
    print("Model Metadata Database Summary")
    print("=" * 40)
    print(f"Total models: {len(metadata)}")
    print(f"Countries represented: {len(geo_dist)}")
    
    print("\nGeographical Distribution:")
    for country, models in geo_dist.items():
        print(f"  {country}: {len(models)} models")
    
    print("\nCost Tier Distribution:")
    cost_tiers = {}
    for model_info in metadata.values():
        tier = model_info.get("cost_tier", "Unknown")
        cost_tiers[tier] = cost_tiers.get(tier, 0) + 1
    
    for tier, count in cost_tiers.items():
        print(f"  {tier}: {count} models")