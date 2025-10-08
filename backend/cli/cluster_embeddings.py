#!/usr/bin/env python3.11
"""
Embedding Clustering CLI

Discover belief frameworks and topics from chunk embeddings.

Usage:
    python cli/cluster_embeddings.py --limit 1000
    python cli/cluster_embeddings.py --user-id <uuid>
    python cli/cluster_embeddings.py --export clusters.json
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.embedding_clustering import EmbeddingClusteringService
from config import settings


async def main():
    parser = argparse.ArgumentParser(description="Cluster chunk embeddings")
    parser.add_argument("--user-id", help="User ID to analyze")
    parser.add_argument("--limit", type=int, help="Limit number of chunks")
    parser.add_argument("--min-cluster-size", type=int, default=15, help="Minimum cluster size")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create database session
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"🧬 Clustering Embeddings - Humanizer Agent\n")
        print(f"Database: {settings.database_url.split('@')[1]}")
        print(f"User: {args.user_id or 'all'}")
        print(f"Limit: {args.limit or 'none'}")
        print(f"Min cluster size: {args.min_cluster_size}\n")

        # Create service
        service = EmbeddingClusteringService(
            min_cluster_size=args.min_cluster_size
        )

        # Fetch embeddings
        print("📊 Fetching embeddings...")
        embeddings, metadata = await service.fetch_embeddings(
            session,
            user_id=args.user_id,
            limit=args.limit,
            min_token_count=15
        )

        if len(embeddings) == 0:
            print("❌ No embeddings found. Generate embeddings first:")
            print("   ./embedgen queue --min-tokens 15")
            print("   ./embedgen process")
            return

        print(f"✓ Fetched {len(embeddings)} embeddings\n")

        # Discover frameworks
        print("🔍 Discovering belief frameworks...")
        results = await service.discover_belief_frameworks(
            session,
            user_id=args.user_id
        )

        print(f"\n{'='*60}")
        print(f"CLUSTERING RESULTS")
        print(f"{'='*60}\n")

        print(f"📈 Total chunks analyzed: {results['n_chunks']}")
        print(f"🎯 Clusters discovered: {results['n_clusters']}")
        print(f"🔇 Noise points: {results['n_noise']}\n")

        # Display cluster summaries
        print(f"{'='*60}")
        print(f"BELIEF FRAMEWORKS")
        print(f"{'='*60}\n")

        for cluster_id, analysis in sorted(results['clusters'].items()):
            print(f"📁 Cluster #{cluster_id} ({analysis['size']} chunks)")
            print(f"   Avg tokens: {analysis['avg_token_count']:.0f}")

            # Top words
            top_words = ", ".join([w['word'] for w in analysis['top_words'][:5]])
            print(f"   Key words: {top_words}")

            # Representative chunk
            rep = analysis['representative_chunk']
            preview = rep['content'][:100].replace('\n', ' ')
            print(f"   Preview: \"{preview}...\"\n")

        # Export if requested
        if args.export:
            export_path = Path(args.export)
            with open(export_path, 'w') as f:
                # Convert numpy arrays to lists for JSON serialization
                json_results = {
                    "n_chunks": results['n_chunks'],
                    "n_clusters": results['n_clusters'],
                    "n_noise": results['n_noise'],
                    "clusters": results['clusters'],
                    "chunk_metadata": results['chunk_metadata'],
                    "parameters": results['parameters']
                }
                json.dump(json_results, f, indent=2, default=str)

            print(f"✓ Exported results to: {export_path}\n")

        # Interpretation
        print(f"{'='*60}")
        print(f"INTERPRETATION")
        print(f"{'='*60}\n")

        print("💡 These clusters represent distinct belief frameworks or topics")
        print("   in your conversation history. Each cluster groups semantically")
        print("   similar chunks that likely share:")
        print("   - PERSONA (voice/perspective)")
        print("   - NAMESPACE (conceptual domain)")
        print("   - STYLE (presentation approach)\n")

        print("🧘 Contemplative Insight:")
        print(f"   You contain {results['n_clusters']} distinct perspectives,")
        print("   each a valid construction. None is 'you' - all are viewpoints")
        print("   you've inhabited. This is non-self (anatta) in action.\n")

        # Suggest next steps
        print(f"{'='*60}")
        print(f"NEXT STEPS")
        print(f"{'='*60}\n")

        print("🎯 Use discovered frameworks for transformations:")
        print(f"   1. Extract framework definitions from cluster centroids")
        print(f"   2. Apply discovered frameworks to new content")
        print(f"   3. Compare frameworks (cluster similarity)\n")

        print("🔬 Advanced analysis:")
        print(f"   - Temporal trajectories (how frameworks shift over time)")
        print(f"   - Bridge topics (chunks connecting distant clusters)")
        print(f"   - Cluster stability (do frameworks persist or evolve?)\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
